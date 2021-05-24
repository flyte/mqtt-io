"""
The main business logic of the server.

Coordinates initialisation of the GPIO, sensor and stream modules, along with getting
and setting their values and data, connecting to MQTT and sending/receiving MQTT messages.
"""

import logging
import signal
from hashlib import sha1
from typing import List, Optional

import paho.mqtt.client as paho  # type: ignore
import trio
from anyio_mqtt import AnyIOMQTTClient, AnyIOMQTTClientConfig
from anyio_mqtt import State as AnyIOMQTTClientState
from trio_typing import TaskStatus

from mqtt_io.events import EventBus
from mqtt_io.mqtt import MQTTClientOptions, MQTTMessageSend, MQTTTLSOptions, MQTTWill
from mqtt_io.types import ConfigType

from .abc import GenericIO
from .gpio import GPIO
from .home_assistant import (
    hass_announce_digital_input,
    hass_announce_digital_output,
    hass_announce_sensor_input,
)
from .sensors import SensorIO
from .stream import StreamIO

_LOG = logging.getLogger(__name__)


class MQTTIO:  # pylint: disable=too-many-instance-attributes
    """
    The main class that represents the business logic of the server.
    """

    def __init__(self, config: ConfigType):
        self.config = config
        self._init_mqtt_config()

        self._trio_token: Optional[trio.lowlevel.TrioToken] = None
        self._main_nursery: Optional[trio.Nursery] = None
        self._mqtt_nursery: Optional[trio.Nursery] = None
        self._mqtt: Optional[AnyIOMQTTClient] = None

        self._shutdown_requested = trio.Event()

        self.event_bus = EventBus()

        self.gpio = GPIO(config, self)
        self.sensor = SensorIO(config, self)
        self.stream = StreamIO(config, self)
        self.io_modules: List[GenericIO] = [self.gpio, self.sensor, self.stream]

    @property
    def nursery(self) -> trio.Nursery:
        """
        The top-level nursery used by the server.
        """
        if self._main_nursery is None:
            raise RuntimeError("Nursery has not been initialised")
        return self._main_nursery

    @property
    def mqtt(self) -> AnyIOMQTTClient:
        """
        The MQTT client.
        """
        if self._mqtt is None:
            raise RuntimeError("MQTT is not initialised")
        return self._mqtt

    @property
    def trio_token(self) -> trio.lowlevel.TrioToken:
        """
        The Trio token for calling back into Trio from external threads.
        """
        if self._trio_token is None:
            raise RuntimeError("Server has not yet been run()")
        return self._trio_token

    def run(self) -> None:
        """
        Run the server.
        """
        trio.run(self.run_async)

    async def run_async(self) -> None:
        """
        Initialise and run the server.
        """
        self._trio_token = trio.lowlevel.current_trio_token()
        try:
            async with trio.open_nursery() as nursery:
                self._main_nursery = nursery

                await nursery.start(self._handle_signals)
                await nursery.start(self.event_bus.run)
                await nursery.start(self._run_mqtt)

                await self.gpio.init()
                await self.sensor.init()
                await self.stream.init()

                self._send_running_msg()
                nursery.start_soon(self._handle_mqtt_client_state_changes)
        finally:
            _LOG.debug("Main nursery exited")

    async def shutdown(self) -> None:
        """
        Shutdown the server cleanly.
        """
        self._shutdown_requested.set()
        await self.mqtt.wait_for_state(AnyIOMQTTClientState.DISCONNECTED)
        self.nursery.cancel_scope.cancel()
        for io_module in self.io_modules:
            _LOG.debug("Cleaning up %s IO module", io_module.__class__.__name__)
            await trio.to_thread.run_sync(io_module.cleanup)

    async def _run_mqtt(
        self, task_status: TaskStatus[None] = trio.TASK_STATUS_IGNORED
    ) -> None:
        """
        Initialise and run the MQTT connection.
        """

        async def handle_messages(client: AnyIOMQTTClient) -> None:
            msg: paho.MQTTMessage
            async for msg in client.messages:
                for io_module in self.io_modules:
                    self.nursery.start_soon(
                        io_module.handle_mqtt_msg, msg.topic, msg.payload
                    )
            _LOG.debug("handle_messages() finished")

        options = self.mqtt_client_options
        client_config = AnyIOMQTTClientConfig(
            dict(client_id=options.client_id, clean_session=options.clean_session)
        )
        try:
            async with AnyIOMQTTClient(client_config) as self._mqtt:
                self._mqtt.enable_logger(logging.getLogger("mqtt"))
                if options.tls_options is not None:
                    self._mqtt.tls_set_context(options.tls_options.ssl_context)
                if options.username is not None:
                    self._mqtt.username_pw_set(options.username, options.password)
                self._mqtt.connect(options.hostname, options.port, options.keepalive)
                if options.will is not None:
                    self._mqtt.will_set(
                        options.will.topic,
                        options.will.payload,
                        options.will.qos,
                        options.will.retain,
                    )
                self.nursery.start_soon(handle_messages, self._mqtt)
                mqtt_config: ConfigType = self.config["mqtt"]
                if "ha_discovery" in mqtt_config:
                    self._ha_discovery_announce(self._mqtt)
                task_status.started()

                await self._shutdown_requested.wait()

                msg_info: paho.MQTTMessageInfo = self._mqtt.publish(
                    "/".join((mqtt_config["topic_prefix"], mqtt_config["status_topic"])),
                    mqtt_config["status_payload_stopped"].encode("utf8"),
                    qos=1,
                    retain=True,
                )
                await trio.to_thread.run_sync(msg_info.wait_for_publish)
                self._mqtt.disconnect()

        finally:
            _LOG.debug("MQTT client closed")

    async def _handle_signals(
        self, task_status: TaskStatus[None] = trio.TASK_STATUS_IGNORED
    ) -> None:
        """
        Catch signals and handle them.
        """
        with trio.open_signal_receiver(signal.SIGINT, signal.SIGQUIT) as signal_aiter:
            task_status.started()
            async for signum in signal_aiter:
                _LOG.warning("Caught signal %s", signum)
                await self.shutdown()

    def _send_running_msg(self) -> None:
        self.mqtt.publish(
            "/".join(
                (
                    self.config["mqtt"]["topic_prefix"],
                    self.config["mqtt"]["status_topic"],
                )
            ),
            self.config["mqtt"]["status_payload_running"].encode("utf8"),
            qos=1,
            retain=True,
        )

    async def _handle_mqtt_client_state_changes(self) -> None:
        """
        Run appropriate code when the MQTT client changes state.
        """
        async for state in self.mqtt.states:
            if state == AnyIOMQTTClientState.CONNECTED:
                self._send_running_msg()

    def _ha_discovery_announce(self, client: AnyIOMQTTClient) -> None:
        """
        Announce our IO configs to Home Assistant.
        """
        messages: List[MQTTMessageSend] = []
        mqtt_config: ConfigType = self.config["mqtt"]

        for in_conf in self.gpio.digital_input_configs.values():
            messages.append(
                hass_announce_digital_input(
                    in_conf, mqtt_config, self.mqtt_client_options
                )
            )
        for out_conf in self.gpio.digital_output_configs.values():
            messages.append(
                hass_announce_digital_output(
                    out_conf, mqtt_config, self.mqtt_client_options
                )
            )
        for sens_conf in self.sensor.sensor_input_configs.values():
            messages.append(
                hass_announce_sensor_input(
                    sens_conf, mqtt_config, self.mqtt_client_options
                )
            )

        for msg in messages:
            client.publish(msg.topic, msg.payload, msg.qos, msg.retain)

    def _init_mqtt_config(self) -> None:
        config: ConfigType = self.config["mqtt"]
        topic_prefix: str = config["topic_prefix"]

        client_id: Optional[str] = config["client_id"]
        if not client_id:
            client_id = "mqtt-io-%s" % sha1(topic_prefix.encode("utf8")).hexdigest()

        tls_enabled: bool = config.get("tls", {}).get("enabled")

        tls_options = None
        if tls_enabled:
            tls_options = MQTTTLSOptions(
                ca_certs=config["tls"].get("ca_certs"),
                certfile=config["tls"].get("certfile"),
                keyfile=config["tls"].get("keyfile"),
                ciphers=config["tls"].get("ciphers"),
            )

        self.mqtt_client_options = MQTTClientOptions(
            hostname=config["host"],
            port=config["port"],
            username=config["user"],
            password=config["password"],
            client_id=client_id,
            keepalive=config["keepalive"],
            clean_session=config["clean_session"],
            tls_options=tls_options,
            will=MQTTWill(
                topic="/".join((topic_prefix, config["status_topic"])),
                payload=config["status_payload_dead"].encode("utf8"),
                qos=1,
                retain=True,
            ),
        )
