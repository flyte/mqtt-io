import logging
from hashlib import sha1
from typing import Any, Dict, List, Optional, Tuple

import paho.mqtt.client as paho
import trio
from anyio_mqtt import AnyIOMQTTClient

from mqtt_io.events import EventBus
from mqtt_io.mqtt import MQTTClientOptions, MQTTMessageSend, MQTTTLSOptions, MQTTWill
from mqtt_io.types import ConfigType

from .abc import GenericIO
from .constants import SEND_SUFFIX, SET_OFF_MS_SUFFIX, SET_ON_MS_SUFFIX, SET_SUFFIX
from .gpio import GPIO
from .home_assistant import (
    hass_announce_digital_input,
    hass_announce_digital_output,
    hass_announce_sensor_input,
)
from .sensors import SensorIO
from .stream import StreamIO

_LOG = logging.getLogger(__name__)


class MQTTIO:
    def __init__(self, config: ConfigType):
        self.config = config
        self._init_mqtt_config()

        self._trio_token: Optional[trio.lowlevel.TrioToken] = None
        self._main_nursery: Optional[trio.Nursery] = None
        self._mqtt_nursery: Optional[trio.Nursery] = None
        self._mqtt: Optional[AnyIOMQTTClient] = None

        self.event_bus = EventBus()

        self.gpio = GPIO(config, self)
        self.sensor = SensorIO(config, self)
        self.stream = StreamIO(config, self)
        self.io_modules: List[GenericIO] = [self.gpio, self.sensor, self.stream]

    @property
    def nursery(self) -> trio.Nursery:
        if self._main_nursery is None:
            raise RuntimeError("Nursery has not been initialised")
        return self._main_nursery

    @property
    def mqtt(self) -> AnyIOMQTTClient:
        if self._mqtt is None:
            raise RuntimeError("MQTT is not initialised")
        return self._mqtt

    @property
    def trio_token(self) -> trio.lowlevel.TrioToken:
        if self._trio_token is None:
            raise RuntimeError("Server has not yet been run()")
        return self._trio_token

    def run(self):

        # signals stuff

        trio.run(self.run_async)

    async def run_async(self):
        self._trio_token = trio.lowlevel.current_trio_token()
        async with trio.open_nursery() as nursery:
            self._main_nursery = nursery

            await nursery.start(self.event_bus.run)
            await nursery.start(self.run_mqtt)

            await self.gpio.init()
            await self.sensor.init()
            await self.stream.init()

    async def run_mqtt(
        self, task_status: trio._core._run._TaskStatus = trio.TASK_STATUS_IGNORED
    ):
        async def handle_messages(client: AnyIOMQTTClient) -> None:
            msg: paho.MQTTMessage
            async for msg in client.messages:
                for io_module in self.io_modules:
                    self.nursery.start_soon(
                        io_module.handle_mqtt_msg, msg.topic, msg.payload
                    )
            _LOG.debug("handle_messages() finished")

        options = self.mqtt_client_options
        async with trio.open_nursery() as nursery:
            self._mqtt_nursery = nursery
            self._mqtt = client = AnyIOMQTTClient(
                nursery,
                dict(client_id=options.client_id, clean_session=options.clean_session),
            )
            self._mqtt.enable_logger(logging.getLogger("mqtt"))
            if options.tls_options is not None:
                client.tls_set_context(options.tls_options.ssl_context)
            if options.username is not None:
                client.username_pw_set(options.username, options.password)
            client.connect(options.hostname, options.port, options.keepalive)
            if options.will is not None:
                client.will_set(
                    options.will.topic,
                    options.will.payload,
                    options.will.qos,
                    options.will.retain,
                )
            nursery.start_soon(handle_messages, client)
            if "ha_discovery" in self.config["mqtt"]:
                self._ha_discovery_announce(client)
            task_status.started()

    def _ha_discovery_announce(self, client: AnyIOMQTTClient) -> None:
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
