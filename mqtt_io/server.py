"""
The main business logic of the server.

Coordinates initialisation of the GPIO, sensor and stream modules, along with getting
and setting their values and data, connecting to MQTT and sending/receiving MQTT messages.
"""

# pylint: enable=duplicate-code
# pylint: disable=too-many-lines

import asyncio
import logging
import signal as signals
import threading
from asyncio.queues import QueueEmpty
from hashlib import sha1
from typing import Any, Dict, List, Optional

from .constants import (
    MQTT_ANNOUNCE_PRIORITY,
    MQTT_PUB_PRIORITY,
    SEND_SUFFIX,
    SET_OFF_MS_SUFFIX,
    SET_ON_MS_SUFFIX,
    SET_SUFFIX,
)
from .events import (
    EventBus,
)
from .gpio import GPIO
from .home_assistant import (
    hass_announce_digital_input,
    hass_announce_digital_output,
    hass_announce_sensor_input,
)
from .mqtt import (
    AbstractMQTTClient,
    MQTTClientOptions,
    MQTTException,
    MQTTMessageSend,
    MQTTTLSOptions,
    MQTTWill,
)
from .sensors import SensorIO
from .stream import StreamIO
from .tasks import TransientTaskManager
from .types import ConfigType
from .utils import PriorityCoro

_LOG = logging.getLogger(__name__)


class MqttIo:  # pylint: disable=too-many-instance-attributes
    """
    The main class that represents the business logic of the server. This is instantiated
    once per config file, of which there is generally only one.
    """

    def __init__(
        self, config: Dict[str, Any], loop: Optional[asyncio.AbstractEventLoop] = None
    ) -> None:
        self.config = config
        self._init_mqtt_config()

        # Synchronisation
        # We've completed our initialisation, connected to MQTT and are ready to send and
        # receive messages.
        self.running: threading.Event = threading.Event()

        # IO functionality
        self.gpio = GPIO(config, self)
        self.sensor = SensorIO(config, self)
        self.stream = StreamIO(config, self)

        self.loop = loop or asyncio.get_event_loop()
        self._main_task: Optional["asyncio.Task[None]"] = None
        self.critical_tasks: List["asyncio.Task[Any]"] = []

        self.transient_task_queue: "TransientTaskManager" = TransientTaskManager()

        self.event_bus = EventBus(self.loop, self.transient_task_queue)
        self.mqtt: Optional[AbstractMQTTClient] = None

        self.mqtt_task_queue: "asyncio.PriorityQueue[PriorityCoro]"
        self.mqtt_connected: asyncio.Event

        self._task_loop: Optional["asyncio.Task[Any]"] = None
        self._connection_loop_task: Optional["asyncio.Task[Any]"] = None

        async def create_loop_resources() -> None:
            """
            Create non-threadsafe resources on the loop we're going to use.
            """
            self.mqtt_task_queue = asyncio.PriorityQueue()
            self.mqtt_connected = asyncio.Event()

        self.loop.run_until_complete(create_loop_resources())

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

    def new_publish_task(self, name: str, retain: bool, data: Any, typ: str) -> None:
        """
        Puts a new Task to publish a message in the mqtt_task_queue
        """
        self.mqtt_task_queue.put_nowait(
            PriorityCoro(
                self._mqtt_publish(
                    MQTTMessageSend(
                        "/".join(
                            (
                                self.config["mqtt"]["topic_prefix"],
                                typ,
                                name,
                            )
                        ),
                        data,
                        retain=retain,
                    )
                ),
                MQTT_PUB_PRIORITY,
            )
        )

    async def _connect_mqtt(self) -> None:
        config: ConfigType = self.config["mqtt"]
        topic_prefix: str = config["topic_prefix"]
        mqtt = AbstractMQTTClient.get_implementation(config["client_module"])(
            self.mqtt_client_options
        )

        _LOG.info("Connecting to MQTT...")
        await mqtt.connect()
        _LOG.info("Connected to MQTT")
        self.mqtt = mqtt
        self.mqtt_task_queue.put_nowait(
            PriorityCoro(
                self._mqtt_publish(
                    MQTTMessageSend(
                        "/".join((topic_prefix, config["status_topic"])),
                        config["status_payload_running"].encode("utf8"),
                        qos=1,
                        retain=True,
                    )
                ),
                MQTT_PUB_PRIORITY,
            )
        )
        self.mqtt_connected.set()

    def _ha_discovery_announce(self) -> None:
        """
        Publish Home Assistant Discovery messages.
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
            self.mqtt_task_queue.put_nowait(
                PriorityCoro(self._mqtt_publish(msg), MQTT_ANNOUNCE_PRIORITY)
            )

    async def mqtt_subscribe(self, topics: List[str]) -> None:
        """
        Subscribe to MQTT topics and output to log for each.
        """
        if not self.mqtt_connected.is_set():
            _LOG.debug("_mqtt_subscribe awaiting MQTT connection")
            await self.mqtt_connected.wait()
            _LOG.debug("_mqtt_subscribe unblocked after MQTT connection")
        if self.mqtt is None:
            raise RuntimeError("MQTT client was None when trying to subscribe.")
        await self.mqtt.subscribe([(topic, 1) for topic in topics])
        for topic in topics:
            _LOG.info("Subscribed to topic: %r", topic)

    async def _mqtt_publish(self, msg: MQTTMessageSend, wait: bool = True) -> None:
        if not self.mqtt_connected.is_set():
            if wait:
                _LOG.debug("_mqtt_publish awaiting MQTT connection")
                await self.mqtt_connected.wait()
                _LOG.debug("_mqtt_publish unblocked after MQTT connection")
        if self.mqtt is None:
            raise RuntimeError("MQTT client was None when trying to publish.")

        msg.debug()

        await self.mqtt.publish(msg)

    # Runtime methods

    async def _handle_mqtt_msg(self, topic: str, payload: bytes) -> None:
        """
        Parse all MQTT messages received on our subscriptions and dispatch actions
        such as changing outputs and sending data to streams accordingly.
        """

        if not any(
            topic.endswith(f"/{x}")
            for x in (SET_SUFFIX, SET_ON_MS_SUFFIX, SET_OFF_MS_SUFFIX, SEND_SUFFIX)
        ):
            _LOG.debug(
                "Ignoring message to topic '%s' which doesn't end with a known suffix",
                topic,
            )
            return

        # Handle digital output message
        if any(
            topic.endswith(f"/{x}")
            for x in (SET_SUFFIX, SET_ON_MS_SUFFIX, SET_OFF_MS_SUFFIX)
        ):
            try:
                payload_str = payload.decode("utf8")
            except UnicodeDecodeError:
                _LOG.warning(
                    "Received MQTT message to a digital output topic '%s' that wasn't unicode.",
                    topic,
                )
                return
            await self.gpio.handle_digital_output_msg(topic, payload_str)

        # Handle stream send message
        if topic.endswith("/send"):
            await self.stream.handle_stream_send_msg(topic, payload)

        # Ignore unknown topics, although we shouldn't get here, because we only subscribe
        # to ones we know.

    # Tasks

    async def _mqtt_task_loop(self) -> None:
        """
        This loop pulls tasks from `self.mqtt_task_queue` and awaits (runs) them, so that
        we don't try to run MQTT tasks before the MQTT connection is initialised.
        """
        if not self.mqtt_connected.is_set():
            _LOG.debug("_mqtt_task_loop awaiting MQTT connection")
            await self.mqtt_connected.wait()
            _LOG.debug("_mqtt_task_loop unblocked after MQTT connection")
        while True:
            entry = await self.mqtt_task_queue.get()
            _LOG.debug(
                "Running MQTT task with priority %s: %s", entry.priority, entry.coro
            )
            try:
                await entry.coro
            except MQTTException:
                raise
            except Exception:  # pylint: disable=broad-except
                _LOG.exception("Exception while handling MQTT task:")
            self.mqtt_task_queue.task_done()

    async def _mqtt_rx_loop(self) -> None:
        if not self.mqtt_connected.is_set():
            _LOG.debug("_mqtt_rx_loop awaiting MQTT connection")
            await self.mqtt_connected.wait()
            _LOG.debug("_mqtt_rx_loop unblocked after MQTT connection")
        while True:
            if self.mqtt is None:
                _LOG.error("Attempted to get MQTT message before client initialised")
                while self.mqtt is None:
                    await asyncio.sleep(1)
                continue
            msg = await self.mqtt.message_queue.get()
            if msg.payload is None:
                _LOG.warning(
                    "Received a message to topic '%r' without a payload", msg.topic
                )
                continue
            try:
                payload_str = msg.payload.decode("utf8")
            except UnicodeDecodeError:
                _LOG.debug("Received non-unicode message on topic %r", msg.topic)
            else:
                _LOG.debug("Received message on topic %r: %r", msg.topic, payload_str)
            await self._handle_mqtt_msg(msg.topic, msg.payload)

    async def _remove_finished_transient_tasks(self) -> None:
        await self.transient_task_queue.loop()

    async def _main_loop(self) -> None:
        self._task_loop = self.loop.create_task(self._remove_finished_transient_tasks())
        self._connection_loop_task = self.loop.create_task(self._connection_loop())
        await asyncio.gather(
            self._task_loop,
            self._connection_loop_task,
        )

    async def _connection_loop(self) -> None:
        reconnect = True
        reconnect_delay = self.config["mqtt"]["reconnect_delay"]
        reconnects_remaining = self.config["mqtt"]["reconnect_count"]
        while reconnect:
            try:
                await self._connect_mqtt()
                reconnects_remaining = self.config["mqtt"]["reconnect_count"]
                self.critical_tasks = [
                    self.loop.create_task(coro)
                    for coro in (
                        self._mqtt_task_loop(),
                        self._mqtt_rx_loop(),
                    )
                ]

                self.running.set()

                if self.config["mqtt"].get("ha_discovery", {}).get("enabled"):
                    self._ha_discovery_announce()

                await asyncio.gather(*self.critical_tasks)

            except asyncio.CancelledError:
                break
            except MQTTException:
                self.mqtt = None
                if reconnects_remaining is not None:
                    reconnect = reconnects_remaining > 0
                    reconnects_remaining -= 1
                _LOG.exception("Connection to MQTT broker failed")
            except Exception:  # pylint: disable=broad-except
                _LOG.exception("Exception in critical task:")
                break

            finally:
                _LOG.debug("Clearing events and cancelling 'critical_tasks'")
                self.running.clear()
                self.mqtt_connected.clear()
                if self.critical_tasks:
                    for task in self.critical_tasks:
                        task.cancel()
                    await asyncio.gather(*self.critical_tasks, return_exceptions=True)
                    _LOG.debug("'critical_tasks' cancelled and gathered")
            if reconnect:
                _LOG.debug(
                    "Waiting for MQTT reconnect delay (%s second(s))", reconnect_delay
                )
                await asyncio.sleep(reconnect_delay)
                _LOG.info(
                    "Reconnecting to MQTT broker (%s retries remaining)",
                    "infinite" if reconnects_remaining is None else reconnects_remaining,
                )
        await self.shutdown()

    # Main entry point

    def run(self) -> None:
        """
        Main entry point into the server which initialises all of the modules, connects to
        MQTT and starts the event loop.
        """

        for sig in (signals.SIGHUP, signals.SIGTERM, signals.SIGINT):

            def signal_handler(sig: "signals.Signals" = sig) -> None:
                if self._main_task is not None:
                    self._main_task.cancel()
                else:
                    _LOG.error("No main task to cancel")

            self.loop.add_signal_handler(sig, signal_handler)

        self.gpio.init()
        self.sensor.init()
        self.stream.init()

        self._main_task = self.loop.create_task(self._main_loop())

        _LOG.debug("Going Asynchronous")
        try:
            self.loop.run_until_complete(self._main_task)
        finally:
            self.loop.close()
            _LOG.debug("Loop closed")
            self.sensor.cleanup()
            self.stream.cleanup()
            self.gpio.cleanup()

        _LOG.debug("run() complete")

    async def shutdown(self) -> None:
        """
        Shut down all of the tasks involved in running the server.
        """
        # Cancel our tasks
        for task in self.critical_tasks:
            task.cancel()
            # let the transient task manager handle the await
            self.transient_task_queue.add_task(task)
        if self._task_loop:
            self._task_loop.cancel()
            _LOG.info("Waiting for our tasks to complete...")
            try:
                await self._task_loop
            except asyncio.CancelledError:
                pass

        # Close any remaining unscheduled mqtt coroutines
        while True:
            try:
                mqtt_coro = self.mqtt_task_queue.get_nowait()
            except QueueEmpty:
                break
            mqtt_coro.coro.close()

        if self.mqtt is not None:
            await self._mqtt_publish(
                MQTTMessageSend(
                    "/".join(
                        (
                            self.config["mqtt"]["topic_prefix"],
                            self.config["mqtt"]["status_topic"],
                        )
                    ),
                    self.config["mqtt"]["status_payload_stopped"].encode("utf8"),
                    qos=1,
                    retain=True,
                ),
                wait=False,
            )
            _LOG.info("Disconnecting from MQTT...")
            await self.mqtt.disconnect()
            _LOG.info("MQTT disconnected")

    @property
    def transient_tasks(self) -> List["asyncio.Task[Any]"]:
        """
        A list of running transient tasks.
        """
        return self.transient_task_queue.tasks

    # Needed for testing - TODO: remove

    def _init_sensor_modules(self) -> None:

        self.sensor.init()

    def _init_gpio_modules(self) -> None:

        self.gpio.init_gpio_modules()

    def _init_digital_outputs(self) -> None:

        self.gpio.init_digital_outputs()

    def _init_digital_inputs(self) -> None:
        self.gpio.init_digital_inputs()
