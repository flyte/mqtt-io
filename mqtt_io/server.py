"""
The main business logic of the server.

Coordinates initialisation of the GPIO, sensor and stream modules, along with getting
and setting their values and data, connecting to MQTT and sending/receiving MQTT messages.
"""

# pylint: enable=duplicate-code
# pylint: disable=too-many-lines

import asyncio
import logging
import re
import signal as signals
import threading
from asyncio.queues import QueueEmpty
from functools import partial
from hashlib import sha1
from importlib import import_module
from typing import Any, Dict, List, Optional, Tuple, Type, Union, overload
from aiomqtt.exceptions import MqttCodeError # type: ignore

import backoff  # type: ignore
from typing_extensions import Literal

from .config import (
    get_main_schema_section,
    validate_and_normalise_config,
    validate_and_normalise_digital_input_config,
    validate_and_normalise_digital_output_config,
    validate_and_normalise_sensor_input_config,
)
from .constants import (
    INPUT_TOPIC,
    MODULE_CLASS_NAMES,
    MODULE_IMPORT_PATH,
    MQTT_ANNOUNCE_PRIORITY,
    MQTT_PUB_PRIORITY,
    MQTT_SUB_PRIORITY,
    OUTPUT_TOPIC,
    SEND_SUFFIX,
    SENSOR_TOPIC,
    SET_OFF_MS_SUFFIX,
    SET_ON_MS_SUFFIX,
    SET_SUFFIX,
    STREAM_TOPIC,
)
from .events import (
    DigitalInputChangedEvent,
    DigitalOutputChangedEvent,
    EventBus,
    SensorReadEvent,
    StreamDataReadEvent,
    StreamDataSentEvent,
    StreamDataSubscribeEvent,
    DigitalSubscribeEvent,
)
from .home_assistant import (
    hass_announce_digital_input,
    hass_announce_digital_output,
    hass_announce_sensor_input,
)
from .modules import install_missing_module_requirements
from .modules.gpio import GenericGPIO, InterruptEdge, InterruptSupport, PinDirection
from .modules.sensor import GenericSensor
from .modules.stream import GenericStream
from .mqtt import (
    AbstractMQTTClient,
    MQTTClientOptions,
    MQTTException,
    MQTTMessageSend,
    MQTTTLSOptions,
    MQTTWill,
)
from .types import ConfigType, PinType, SensorValueType
from .utils import PriorityCoro, create_unawaited_task_threadsafe

_LOG = logging.getLogger(__name__)


@overload
def _init_module(
    module_config: Dict[str, Dict[str, Any]],
    module_type: Literal["gpio"],
    install_requirements: bool,
) -> GenericGPIO:
    ...  # pragma: no cover


@overload
def _init_module(
    module_config: Dict[str, Dict[str, Any]],
    module_type: Literal["sensor"],
    install_requirements: bool,
) -> GenericSensor:
    ...  # pragma: no cover


@overload
def _init_module(
    module_config: Dict[str, Dict[str, Any]],
    module_type: Literal["stream"],
    install_requirements: bool,
) -> GenericStream:
    ...  # pragma: no cover


def _init_module(
    module_config: Dict[str, Dict[str, Any]], module_type: str, install_requirements: bool
) -> Union[GenericGPIO, GenericSensor, GenericStream]:
    """
    Initialise a module by:
    - Importing it
    - Validating its config
    - Installing any missing requirements for it
    - Instantiating its class
    """
    module = import_module(
        "%s.%s.%s" % (MODULE_IMPORT_PATH, module_type, module_config["module"])
    )
    # Doesn't need to be a deep copy because we're not mutating the base rules
    module_schema = get_main_schema_section(f"{module_type}_modules")
    # Add the module's config schema to the base schema
    module_schema.update(getattr(module, "CONFIG_SCHEMA", {}))
    module_config = validate_and_normalise_config(module_config, module_schema)
    if install_requirements:
        install_missing_module_requirements(module)
    module_class: Type[Union[GenericGPIO, GenericSensor, GenericStream]] = getattr(
        module, MODULE_CLASS_NAMES[module_type]
    )
    return module_class(module_config)


def output_name_from_topic(topic: str, prefix: str, topic_type: str) -> str:
    """
    Parses an MQTT topic and returns the name of the output that the message relates to.
    """
    match = re.match(f"^{prefix}/{topic_type}/(.+?)/.+$", topic)
    if match is None:
        raise ValueError("Topic %r does not adhere to expected structure" % topic)
    return match.group(1)


class MqttIo:  # pylint: disable=too-many-instance-attributes
    """
    The main class that represents the business logic of the server. This is instantiated
    once per config file, of which there is generally only one.
    """

    def __init__(
        self, config: Dict[str, Any], loop: Optional[asyncio.AbstractEventLoop] = None
    ) -> None:
        """
        Initializes the class with the given configuration and event loop.

        Parameters:
            config (Dict[str, Any]): The configuration for the class.
            loop (Optional[asyncio.AbstractEventLoop]): The event loop to use.
            If not provided, the default event loop will be used.

        Returns:
            None
        """
        self.config = config
        self._init_mqtt_config()

        # Synchronisation
        # We've completed our initialisation, connected to MQTT and are ready to send and
        # receive messages.
        self.running: threading.Event = threading.Event()

        # GPIO
        self.gpio_configs: Dict[str, ConfigType] = {}
        self.digital_input_configs: Dict[str, ConfigType] = {}
        self.digital_output_configs: Dict[str, ConfigType] = {}
        self.gpio_modules: Dict[str, GenericGPIO] = {}

        # Sensor
        self.sensor_configs: Dict[str, ConfigType] = {}
        self.sensor_input_configs: Dict[str, ConfigType] = {}
        self.sensor_modules: Dict[str, GenericSensor] = {}

        # Stream
        self.stream_configs: Dict[str, ConfigType] = {}
        self.stream_modules: Dict[str, GenericStream] = {}
        self.stream_output_queues = {}  # type: Dict[str, asyncio.Queue[bytes]]

        self.gpio_output_queues = (
            {}
        )  # type: Dict[str, asyncio.Queue[Tuple[ConfigType, str]]]

        self.loop = loop or asyncio.get_event_loop()
        self._main_task: Optional["asyncio.Task[None]"] = None
        self.critical_tasks: List["asyncio.Task[Any]"] = []
        self.transient_tasks: List["asyncio.Task[Any]"] = []

        self.event_bus = EventBus(self.loop, self.transient_tasks)
        self.mqtt: Optional[AbstractMQTTClient] = None
        self.interrupt_locks: Dict[str, threading.Lock] = {}

        self.mqtt_task_queue: "asyncio.PriorityQueue[PriorityCoro]"
        self.mqtt_connected: asyncio.Event

        async def create_loop_resources() -> None:
            """
            Create non-threadsafe resources on the loop we're going to use.
            """
            self.mqtt_task_queue = asyncio.PriorityQueue()
            self.mqtt_connected = asyncio.Event()

        self.loop.run_until_complete(create_loop_resources())

    def _init_mqtt_config(self) -> None:
        """
        Initializes the MQTT configuration.

        This function retrieves the MQTT configuration from the application's
        main configuration file and performs the necessary setup tasks.
        It sets the topic prefix for MQTT messages, replaces the '<ip>' placeholder
        in the topic prefix with the IP address of the 'wlan0' interface,
        generates a client ID if not provided, and configures TLS options if enabled.

        Parameters:
            None

        Returns:
            None
        """
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

    # Init methods

    def _init_gpio_modules(self) -> None:
        """
        Initialise GPIO modules.
        """
        self.gpio_configs = {x["name"]: x for x in self.config["gpio_modules"]}
        self.gpio_modules = {}
        for gpio_config in self.config["gpio_modules"]:
            self.gpio_modules[gpio_config["name"]] = _init_module(
                gpio_config, "gpio", self.config["options"]["install_requirements"]
            )

    def _init_sensor_modules(self) -> None:
        """
        Initialise Sensor modules.
        """
        self.sensor_configs = {x["name"]: x for x in self.config["sensor_modules"]}
        self.sensor_modules = {}
        for sens_config in self.config["sensor_modules"]:
            self.sensor_modules[sens_config["name"]] = _init_module(
                sens_config, "sensor", self.config["options"]["install_requirements"]
            )

    def _init_stream_modules(self) -> None:
        """
        Initialise Stream modules.
        """

        # TODO: Tasks pending completion -@flyte at 01/03/2021, 14:40:10
        # Only publish if read: true and only subscribe if write: true

        async def publish_stream_data_callback(event: StreamDataReadEvent) -> None:
            stream_conf = self.stream_configs[event.stream_name]
            self.mqtt_task_queue.put_nowait(
                PriorityCoro(
                    self._mqtt_publish(
                        MQTTMessageSend(
                            "/".join(
                                (
                                    self.config["mqtt"]["topic_prefix"],
                                    STREAM_TOPIC,
                                    stream_conf["name"],
                                )
                            ),
                            event.data,
                            retain=stream_conf["retain"],
                        )
                    ),
                    MQTT_PUB_PRIORITY,
                )
            )

        self.event_bus.subscribe(StreamDataReadEvent, publish_stream_data_callback)

        self.stream_configs = {x["name"]: x for x in self.config["stream_modules"]}
        self.stream_modules = {}
        for stream_conf in self.config["stream_modules"]:
            stream_module = _init_module(
                stream_conf, "stream", self.config["options"]["install_requirements"]
            )
            self.stream_modules[stream_conf["name"]] = stream_module

            self.transient_tasks.append(
                self.loop.create_task(self.stream_poller(stream_module, stream_conf))
            )

            async def create_stream_output_queue(
                stream_conf: ConfigType = stream_conf,
            ) -> None:
                """
                Set up a stream output queue.
                """
                queue = asyncio.Queue()  # type: asyncio.Queue[bytes]
                self.stream_output_queues[stream_conf["name"]] = queue

            self.loop.run_until_complete(create_stream_output_queue())

            # Queue a stream output loop task
            self.transient_tasks.append(
                self.loop.create_task(
                    # Use partial to avoid late binding closure
                    partial(
                        self.stream_output_loop,
                        stream_module,
                        stream_conf,
                        self.stream_output_queues[stream_conf["name"]],
                    )()
                )
            )

        # Subscribe call back funktion: Subscribe to stream send topics
        async def subscribe_callback(event: StreamDataSubscribeEvent) -> None:
            sub_topics: List[str] = []
            for stream_conf in self.config["stream_modules"]:
                sub_topics.append(
                    "/".join(
                        (
                            self.config["mqtt"]["topic_prefix"],
                            STREAM_TOPIC,
                            stream_conf["name"],
                            SEND_SUFFIX,
                        )
                    )
                )

            if sub_topics:
                self.mqtt_task_queue.put_nowait(
                    PriorityCoro(self._mqtt_subscribe(sub_topics), MQTT_SUB_PRIORITY)
                )

        self.event_bus.subscribe(StreamDataSubscribeEvent, subscribe_callback)

    def _init_digital_inputs(self) -> None:
        """
        Initialise all of the digital inputs by doing the following:
        - Create a closure function to publish an MQTT message on DigitalInputchangedEvent
        For each of the inputs:
        - Set up the self.digital_input_configs dict
        - Call the module's setup_pin() method
        - Optionally start an async task that continuously polls the input for changes
        - Optionally call the module's setup_interrupt() method, with a software callback
          if it's supported.
        """
        # Set up MQTT publish callback for input event.
        # Needs to be a function, not a method, hence the closure function.
        async def publish_callback(event: DigitalInputChangedEvent) -> None:
            in_conf = self.digital_input_configs[event.input_name]
            value = event.to_value != in_conf["inverted"]
            val = in_conf["on_payload"] if value else in_conf["off_payload"]
            self.mqtt_task_queue.put_nowait(
                PriorityCoro(
                    self._mqtt_publish(
                        MQTTMessageSend(
                            "/".join(
                                (
                                    self.config["mqtt"]["topic_prefix"],
                                    INPUT_TOPIC,
                                    event.input_name,
                                )
                            ),
                            val.encode("utf8"),
                            retain=in_conf["retain"],
                        )
                    ),
                    MQTT_PUB_PRIORITY,
                )
            )

        self.event_bus.subscribe(DigitalInputChangedEvent, publish_callback)

        for in_conf in self.config["digital_inputs"]:
            gpio_module = self.gpio_modules[in_conf["module"]]
            in_conf = validate_and_normalise_digital_input_config(in_conf, gpio_module)
            self.digital_input_configs[in_conf["name"]] = in_conf

            gpio_module.setup_pin_internal(PinDirection.INPUT, in_conf)

            interrupt = in_conf.get("interrupt")
            interrupt_for = in_conf.get("interrupt_for")

            # Only start the poller task if this _isn't_ set up with an interrupt, or if
            # it _is_ an interrupt, but it's used for triggering remote interrupts.
            if interrupt is None or (
                interrupt_for and in_conf["poll_when_interrupt_for"]
            ):
                self.transient_tasks.append(
                    self.loop.create_task(
                        partial(self.digital_input_poller, gpio_module, in_conf)()
                    )
                )

            if interrupt:
                edge = {
                    "rising": InterruptEdge.RISING,
                    "falling": InterruptEdge.FALLING,
                    "both": InterruptEdge.BOTH,
                }[interrupt]
                callback = None
                if gpio_module.INTERRUPT_SUPPORT & InterruptSupport.SOFTWARE_CALLBACK:
                    self.interrupt_locks[in_conf["name"]] = threading.Lock()
                    # If it's a software callback interrupt, then supply
                    # partial(self.interrupt_callback, module, in_conf["pin"])
                    # as the callback.
                    callback = partial(
                        self.interrupt_callback, gpio_module, in_conf["pin"]
                    )
                gpio_module.setup_interrupt_internal(
                    in_conf["pin"], edge, in_conf, callback=callback
                )

    def _init_digital_outputs(self) -> None:
        """
        Initializes the digital outputs.

        This function sets up the MQTT publish callback for the output event.
        It creates a digital output queue on the right loop for each module.
        It subscribes to outputs when MQTT is initialized.
        It also fires DigitalOutputChangedEvents for the initial values of
        outputs if required, and reads and publishes the actual pin state
        if no publish_initial is requested.

        Parameters:
            None

        Returns:
            None
        """
        # Set up MQTT publish callback for output event
        async def publish_callback(event: DigitalOutputChangedEvent) -> None:
            """
            Publishes a callback function for the given DigitalOutputChangedEvent.

            Args:
                event (DigitalOutputChangedEvent): The event object containing the details
                of the digital output change.

            Returns:
                None
            """
            out_conf = self.digital_output_configs[event.output_name]
            val = out_conf["on_payload"] if event.to_value else out_conf["off_payload"]
            self.mqtt_task_queue.put_nowait(
                PriorityCoro(
                    self._mqtt_publish(
                        MQTTMessageSend(
                            "/".join(
                                (
                                    self.config["mqtt"]["topic_prefix"],
                                    "output",
                                    event.output_name,
                                )
                            ),
                            val.encode("utf8"),
                            retain=out_conf["retain"],
                        )
                    ),
                    MQTT_PUB_PRIORITY,
                )
            )

        self.event_bus.subscribe(DigitalOutputChangedEvent, publish_callback)

        for out_conf in self.config["digital_outputs"]:
            gpio_module = self.gpio_modules[out_conf["module"]]
            out_conf = validate_and_normalise_digital_output_config(out_conf, gpio_module)
            self.digital_output_configs[out_conf["name"]] = out_conf

            gpio_module.setup_pin_internal(PinDirection.OUTPUT, out_conf)

            # Create queues for each module with an output
            if out_conf["module"] not in self.gpio_output_queues:

                async def create_digital_output_queue(
                    out_conf: ConfigType = out_conf,
                ) -> None:
                    """
                    Create digital output queue on the right loop.
                    """
                    queue = asyncio.Queue()  # type: asyncio.Queue[Tuple[ConfigType, str]]
                    self.gpio_output_queues[out_conf["module"]] = queue

                self.loop.run_until_complete(create_digital_output_queue())

                # Use partial to avoid late binding closure
                self.transient_tasks.append(
                    self.loop.create_task(
                        partial(
                            self.digital_output_loop,
                            gpio_module,
                            self.gpio_output_queues[out_conf["module"]],
                        )()
                    )
                )

            # Fire DigitalOutputChangedEvents for initial values of outputs if required
            if out_conf["publish_initial"]:
                self.event_bus.fire(
                    DigitalOutputChangedEvent(
                        out_conf["name"],
                        out_conf["initial"]
                        == ("low" if out_conf["inverted"] else "high"),
                    )
                )
            else:
                # Read and publish actual pin state if no publish_initial requested
                raw_value = gpio_module.get_pin(out_conf["pin"])
                value = raw_value != out_conf["inverted"]
                _LOG.info(
                    "Digital output '%s' current value is %s (raw: %s)",
                    out_conf["name"],
                    value,
                    raw_value,
                )
                self.event_bus.fire(DigitalOutputChangedEvent(out_conf["name"], value))

        # Subscribe call back funktion: Add tasks to subscribe to outputs when MQTT is initialised
        async def subscribe_callback(event: DigitalSubscribeEvent) -> None:
            for out_conf in self.config["digital_outputs"]:
                topics = []
                for suffix in (SET_SUFFIX, SET_ON_MS_SUFFIX, SET_OFF_MS_SUFFIX):
                    topics.append(
                        "/".join(
                            (
                                self.config["mqtt"]["topic_prefix"],
                                OUTPUT_TOPIC,
                                out_conf["name"],
                                suffix,
                            )
                        )
                    )
                self.mqtt_task_queue.put_nowait(
                    PriorityCoro(self._mqtt_subscribe(topics), MQTT_SUB_PRIORITY)
                )

        self.event_bus.subscribe(DigitalSubscribeEvent, subscribe_callback)

    def _init_sensor_inputs(self) -> None:
        """
        Initializes the sensor inputs for the class.

        Parameters:
            None

        Returns:
            None
        """
        async def publish_sensor_callback(event: SensorReadEvent) -> None:
            """
            Publishes a sensor callback event to the MQTT broker.

            Args:
                event (SensorReadEvent): The event object containing the sensor data.

            Returns:
                None
            """
            sens_conf = self.sensor_input_configs[event.sensor_name]
            digits: int = sens_conf["digits"]
            self.mqtt_task_queue.put_nowait(
                PriorityCoro(
                    self._mqtt_publish(
                        MQTTMessageSend(
                            "/".join(
                                (
                                    self.config["mqtt"]["topic_prefix"],
                                    SENSOR_TOPIC,
                                    event.sensor_name,
                                )
                            ),
                            f"{event.value:.{digits}f}".encode("utf8"),
                            retain=sens_conf["retain"],
                        )
                    ),
                    MQTT_PUB_PRIORITY,
                )
            )

        self.event_bus.subscribe(SensorReadEvent, publish_sensor_callback)

        for sens_conf in self.config["sensor_inputs"]:
            sensor_module = self.sensor_modules[sens_conf["module"]]
            sens_conf = validate_and_normalise_sensor_input_config(
                sens_conf, sensor_module
            )
            self.sensor_input_configs[sens_conf["name"]] = sens_conf

            sensor_module.setup_sensor(sens_conf)

            # Use default args to the function to get around the late binding closures
            async def poll_sensor(
                sensor_module: GenericSensor = sensor_module,
                sens_conf: ConfigType = sens_conf,
            ) -> None:
                """
                Asynchronously polls a sensor to retrieve its value at regular intervals.

                Args:
                    sensor_module (Optional[GenericSensor]): The sensor module to use.
                    Defaults to the sensor_module provided during function call.
                    sens_conf (Optional[ConfigType]): The configuration for the sensor.
                    Defaults to the sens_conf provided during function call.

                Returns:
                    None

                """
                @backoff.on_exception(  # type: ignore
                    backoff.expo, Exception, max_time=sens_conf["interval"]
                )
                @backoff.on_predicate(  # type: ignore
                    backoff.expo, lambda x: x is None, max_time=sens_conf["interval"]
                )
                async def get_sensor_value(
                    sensor_module: GenericSensor = sensor_module,
                    sens_conf: ConfigType = sens_conf,
                ) -> SensorValueType:
                    """
                    A decorator that applies exponential backoff to the function `get_sensor_value`.

                    Parameters:
                        sensor_module (GenericSensor): The sensor module to use for getting
                            the sensor value.
                        sens_conf (ConfigType): The configuration for the sensor.

                    Returns:
                        SensorValueType: The value retrieved from the sensor.
                    """
                    return await sensor_module.async_get_value(sens_conf)

                while True:
                    value = None
                    try:
                        value = await get_sensor_value()
                    except Exception:  # pylint: disable=broad-except
                        _LOG.exception(
                            "Exception when retrieving value from sensor %r:",
                            sens_conf["name"],
                        )
                    if value is not None:
                        value = round(value, sens_conf["digits"])
                        _LOG.info(
                            "Read sensor '%s' value of %s", sens_conf["name"], value
                        )
                        self.event_bus.fire(SensorReadEvent(sens_conf["name"], value))
                    await asyncio.sleep(sens_conf["interval"])

            self.transient_tasks.append(self.loop.create_task(poll_sensor()))

    async def _connect_mqtt(self) -> None:
        """
        Connects to the MQTT broker and sets up the necessary configurations.

        Returns:
            None
        """
        config: ConfigType = self.config["mqtt"]
        topic_prefix: str = config["topic_prefix"]
        self.mqtt = AbstractMQTTClient.get_implementation(config["client_module"])(
            self.mqtt_client_options
        )

        _LOG.info("Connecting to MQTT...")
        await self.mqtt.connect()
        _LOG.info("Connected to MQTT")

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
        self.event_bus.fire(StreamDataSubscribeEvent())
        self.event_bus.fire(DigitalSubscribeEvent())


    def _ha_discovery_announce(self) -> None:
        """
        Publish Home Assistant Discovery messages.
        """
        messages: List[MQTTMessageSend] = []
        mqtt_config: ConfigType = self.config["mqtt"]

        for in_conf in self.digital_input_configs.values():
            messages.append(
                hass_announce_digital_input(
                    in_conf, mqtt_config, self.mqtt_client_options
                )
            )
        for out_conf in self.digital_output_configs.values():
            messages.append(
                hass_announce_digital_output(
                    out_conf, mqtt_config, self.mqtt_client_options
                )
            )
        for sens_conf in self.sensor_input_configs.values():
            messages.append(
                hass_announce_sensor_input(
                    sens_conf, mqtt_config, self.mqtt_client_options
                )
            )
        for msg in messages:
            self.mqtt_task_queue.put_nowait(
                PriorityCoro(self._mqtt_publish(msg), MQTT_ANNOUNCE_PRIORITY)
            )

    async def _mqtt_subscribe(self, topics: List[str]) -> None:
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
        """
        Publishes an MQTT message.

        Args:
            msg (MQTTMessageSend): The MQTT message to publish.
            wait (bool, optional): Whether to wait for MQTT connection before publishing.
            Defaults to True.

        Raises:
            RuntimeError: If the MQTT client is None.

        Returns:
            None
        """
        if not self.mqtt_connected.is_set():
            if wait:
                _LOG.debug("_mqtt_publish awaiting MQTT connection")
                await self.mqtt_connected.wait()
                _LOG.debug("_mqtt_publish unblocked after MQTT connection")
        if self.mqtt is None:
            raise RuntimeError("MQTT client was None when trying to publish.")

        if msg.payload is None:
            _LOG.debug("Publishing MQTT message on topic %r with no payload", msg.topic)
        elif isinstance(msg.payload, (bytearray, bytes)):
            try:
                payload = msg.payload.decode("utf8")
            except UnicodeDecodeError:
                _LOG.debug(
                    "Publishing MQTT message on topic %r with non-unicode payload",
                    msg.topic,
                )
            else:
                _LOG.debug(
                    "Publishing MQTT message on topic %r: %r", msg.topic, payload
                )
        else:
            _LOG.debug(
                "Publishing MQTT message on topic %r: %r", msg.topic, payload
            )

        await self.mqtt.publish(msg)

    # Runtime methods

    async def _handle_digital_input_value(
        self,
        in_conf: ConfigType,
        value: bool,
        last_value: Optional[bool],
    ) -> None:
        """
        Handles values read from a digital input.

        Fires a DigitalInputchangedEvent when it changes.

        This function also helps maintain the working state of pins which are configured
        as interrupts for other pins by checking if it's in the 'triggered' state. This
        could mean that the interrupt callback code didn't fire when the pin changed
        state. If that happens, you can end up in a deadlock where the pin remains in that
        state until the remote interrupt is 'handled', which would be never, unless this
        loop polls the 'triggered' value and calls the interupt handling code itself.

        If the interrupt lock is not acquired, then it means that the interrupt is already
        being handled, so we can check again on the next poll.
        """
        if value != last_value:
            _LOG.info("Digital input '%s' value changed to %s", in_conf["name"], value)
            self.event_bus.fire(
                DigitalInputChangedEvent(in_conf["name"], last_value, value)
            )
        # If the value is now the same as the 'interrupt' value (falling, rising)
        # and we're a remote interrupt then just trigger the remote interrupt
        interrupt = in_conf.get("interrupt")
        interrupt_for = in_conf.get("interrupt_for")
        if not interrupt or not interrupt_for:
            return
        if not any(
            (
                interrupt == "rising" and value,
                interrupt == "falling" and not value,
                # Doesn't work for 'both' because there's no one 'triggered' state
                # to check if we're stuck in.
                # interrupt == "both",
            )
        ):
            return
        interrupt_lock = self.interrupt_locks[in_conf["name"]]
        if not interrupt_lock.acquire(blocking=False):
            _LOG.debug(
                (
                    "Polled an interrupt value on pin '%s', but we're "
                    "not triggering the remote interrupt because we're "
                    "already handling it."
                ),
                in_conf["name"],
            )
            return
        _LOG.debug(
            "Polled value of %s on '%s' triggered remote interrupt",
            value,
            in_conf["name"],
        )
        self.handle_remote_interrupt(interrupt_for, interrupt_lock)

    async def digital_input_poller(
        self, module: GenericGPIO, in_conf: ConfigType
    ) -> None:
        """
        Polls a single digital input for changes and calls the handler function when it's
        been read.
        """
        last_value: Optional[bool] = None
        while True:
            value = await module.async_get_pin(in_conf["pin"])
            await self._handle_digital_input_value(in_conf, value, last_value)
            last_value = value
            await asyncio.sleep(in_conf["poll_interval"])

    async def stream_poller(self, module: GenericStream, stream_conf: ConfigType) -> None:
        """
        Poll a stream at a given interval and fire the StreamDataReadEvent with read data.
        """
        while True:
            try:
                data = await module.async_read()
            except Exception:  # pylint: disable=broad-except
                _LOG.exception(
                    "Exception while polling stream '%s':", stream_conf["name"]
                )
            else:
                if data is not None:
                    self.event_bus.fire(StreamDataReadEvent(stream_conf["name"], data))
            await asyncio.sleep(stream_conf["read_interval"])

    def interrupt_callback(
        self,
        module: GenericGPIO,
        pin: PinType,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """
        This function is passed in to any GPIO library that provides software callbacks
        called on interrupt. It's passed to the GPIO library's interrupt setup function
        with its 'module' and 'pin' parameters already filled by partial(), so that
        any *args and **kwargs supplied by the GPIO library will get passed directly
        back to our GPIO module's get_interrupt_value() method.

        If the pin is configured as a remote interrupt for another pin or pins, then the
        execution, along with the interrupt lock is handed off to
        self.handle_remote_interrupt(), instead of getting the pin value, firing the
        DigitalInputChangedEvent and unlocking the interrupt lock.

        This can potentially be called from any thread.
        """
        pin_name = module.pin_configs[pin]["name"]
        if not self.running.is_set():
            # Not yet ready to handle interrupts
            _LOG.warning(
                "Ignored interrupt from pin %r as we're not fully initialised", pin_name
            )
            return
        interrupt_lock = self.interrupt_locks[pin_name]
        if not interrupt_lock.acquire(blocking=False):
            # This will only happen when the pin is configured with interrupt_for, as we
            # release the lock locally otherwise.
            # Hopefully it won't happen at all, but if we miss this interrupt then
            # the poller will notice that the interrupt is triggered and it'll trigger
            # the handling of the remote interrupt anyway, once this lock has been
            # released when the remote interrupt handling tasks have all finished.
            _LOG.warning(
                (
                    "Ignoring interrupt on pin '%s' because we're already busy "
                    "processing one."
                ),
                pin_name,
            )
            return
        remote_interrupt_for_pin_names: List[str] = []
        try:
            _LOG.info("Handling interrupt callback on pin '%s'", pin_name)
            remote_interrupt_for_pin_names = module.remote_interrupt_for(pin)

            if remote_interrupt_for_pin_names:
                _LOG.debug("Interrupt on '%s' triggered remote interrupt.", pin_name)
                self.handle_remote_interrupt(
                    remote_interrupt_for_pin_names, interrupt_lock
                )
                return
            _LOG.debug("Interrupt is for the '%s' pin itself", pin_name)
            value = module.get_interrupt_value(pin, *args, **kwargs)
            self.event_bus.fire(DigitalInputChangedEvent(pin_name, None, value))
        finally:
            if not remote_interrupt_for_pin_names:
                interrupt_lock.release()

    def handle_remote_interrupt(
        self, pin_names: List[str], interrupt_lock: threading.Lock
    ) -> None:
        """
        Adds tasks to the event loop to go off and get the values for the pin(s) which have
        triggered a remote pin's interrupt logic.

        The pin_names are organised by module, then a task is created to pass the list of
        pins to get values for to the module that handles them, and fire a
        DigitalInputChangedEvent for each of the pin values.

        Once all of these tasks have completed, the interrupt lock is released.
        """
        # IDEA: Possible implementations -@flyte at 30/01/2021, 16:09:35
        # Does the interrupt_for module say that its interrupt pin will be held low
        # until the interrupt register is read, or does it just pulse its interrupt
        # pin?
        _LOG.debug("Interrupt is for pins: '%s'", "', '".join(pin_names))
        remote_modules_and_pins: Dict[GenericGPIO, List[PinType]] = {}
        for remote_pin_name in pin_names:
            in_conf = self.digital_input_configs[remote_pin_name]
            remote_module = self.gpio_modules[in_conf["module"]]
            remote_modules_and_pins.setdefault(remote_module, []).append(in_conf["pin"])

        remote_interrupt_tasks = []
        for remote_module, pins in remote_modules_and_pins.items():

            async def handle_remote_interrupt_task(
                remote_module: GenericGPIO = remote_module, pins: List[PinType] = pins
            ) -> None:
                """
                Ask the GPIO module to fetch the values of the specified pins, because
                they caused an interrupt on another module's pin, presumably because
                the module's interrupt line was connected to it.

                Fire a DigitalInputChangedEvent for each of the pins' values returned
                because we don't really know if they changed or not.
                """
                interrupt_values = await remote_module.get_interrupt_values_remote(pins)
                for pin, value in interrupt_values.items():
                    remote_pin_name = remote_module.pin_configs[pin]["name"]
                    self.event_bus.fire(
                        DigitalInputChangedEvent(remote_pin_name, None, value)
                    )

            remote_interrupt_tasks.append(handle_remote_interrupt_task())

        async def await_remote_interrupts() -> None:
            """
            Await all of the remote interrupt tasks so that we can release the interrupt
            lock afterwards.
            """
            try:
                await asyncio.gather(*remote_interrupt_tasks)
            finally:
                interrupt_lock.release()

        create_unawaited_task_threadsafe(
            self.loop, self.transient_tasks, await_remote_interrupts()
        )

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
            await self._handle_digital_output_msg(topic, payload_str)

        # Handle stream send message
        if topic.endswith("/send"):
            await self._handle_stream_send_msg(topic, payload)

        # Ignore unknown topics, although we shouldn't get here, because we only subscribe
        # to ones we know.

    async def _handle_digital_output_msg(self, topic: str, payload: str) -> None:
        """
        Handle an MQTT message that intends to set a digital output's state.
        """
        topic_prefix: str = self.config["mqtt"]["topic_prefix"]
        try:
            output_name = output_name_from_topic(topic, topic_prefix, OUTPUT_TOPIC)
        except ValueError as exc:
            _LOG.warning("Unable to parse digital output name from topic: %s", exc)
            return
        try:
            out_conf = self.digital_output_configs[output_name]
        except KeyError:
            _LOG.warning("No digital output config found named %r", output_name)
            return
        try:
            module = self.gpio_modules[out_conf["module"]]
        except KeyError:
            _LOG.warning("No GPIO module config found named %r", out_conf["module"])
            return
        if topic.endswith("/%s" % SET_SUFFIX):
            # This is a message to set a digital output to a given value
            self.gpio_output_queues[out_conf["module"]].put_nowait((out_conf, payload))
        else:
            # This must be a set_on_ms or set_off_ms topic
            desired_value = topic.endswith("/%s" % SET_ON_MS_SUFFIX)

            async def set_ms() -> None:
                """
                Create this task to directly set the outputs, as we don't want to tie up
                the set_digital_output loop. Creating a bespoke task for the job is the
                simplest and most effective way of leveraging the asyncio framework.
                """
                try:
                    secs = float(payload) / 1000
                except ValueError:
                    _LOG.warning(
                        "Unable to parse ms value as float from payload %r", payload
                    )
                    return
                _LOG.info(
                    "Turning output '%s' %s for %s second(s)",
                    out_conf["name"],
                    "on" if desired_value else "off",
                    secs,
                )
                await self.set_digital_output(module, out_conf, desired_value)
                await asyncio.sleep(secs)
                _LOG.info(
                    "Turning output '%s' %s after %s second(s) elapsed",
                    out_conf["name"],
                    "off" if desired_value else "on",
                    secs,
                )
                await self.set_digital_output(module, out_conf, not desired_value)

            task = self.loop.create_task(set_ms())
            self.transient_tasks.append(task)

    async def _handle_stream_send_msg(self, topic: str, payload: bytes) -> None:
        try:
            stream_name = output_name_from_topic(
                topic, self.config["mqtt"]["topic_prefix"], STREAM_TOPIC
            )
        except ValueError as exc:
            _LOG.warning("Unable to parse stream name from topic: %s", exc)
            return
        try:
            self.stream_output_queues[stream_name].put_nowait(payload)
        except KeyError:
            _LOG.warning("No stream output queue found named %r", stream_name)

    async def set_digital_output(
        self, module: GenericGPIO, output_config: ConfigType, value: bool
    ) -> None:
        """
        Set a digital output, taking into account whether it's configured
        to be inverted.
        """
        set_value = value != output_config["inverted"]
        await module.async_set_pin(output_config["pin"], set_value)
        _LOG.info(
            "Digital output '%s' set to %s (%s)",
            output_config["name"],
            set_value,
            "on" if value else "off",
        )
        self.event_bus.fire(DigitalOutputChangedEvent(output_config["name"], value))

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

    async def _mqtt_keep_alive_loop(self) -> None:
        """
        Publish a message on the status topic regularly to keep the connection alive.
        This is a workaround for 2 different problems:
        - keepalive was not implemented in early versions of asyncio_mqtt
        - due to the way we receive messages asynchronously in our own queue we are not able
          to capture the disconnected exception and trigger the reconnection. This publish call
          will trigger the exception if the connection was lost and reconnect. (Issue #282)
        """
        config: ConfigType = self.config["mqtt"]
        topic_prefix: str = config["topic_prefix"]
        if not self.mqtt_connected.is_set():
            _LOG.debug("_mqtt_keep_alive_loop awaiting MQTT connection")
            await self.mqtt_connected.wait()
            _LOG.debug("_mqtt_keep_alive_loop unblocked after MQTT connection")
        while True:
            if self.mqtt is None:
                _LOG.error("Attempted to ping MQTT server before client initialised")
                while self.mqtt is None:
                    await asyncio.sleep(1)
                continue
            await self.mqtt.publish(MQTTMessageSend(
                        "/".join((topic_prefix, config["status_topic"])),
                        config["status_payload_running"].encode("utf8"),
                        qos=1,
                        retain=True,
                    ))
            await asyncio.sleep(config["keepalive"])

    async def _mqtt_rx_loop(self) -> None:
        """
        Asynchronous function that runs a loop to receive MQTT messages.

        The function first checks if the MQTT connection is established. If not, it awaits
        the connection before proceeding. Once the connection is established, the function
        enters an infinite loop.

        Within the loop, the function checks if the MQTT client is initialized. If not, it
        logs an error message and waits for the client to be initialized before proceeding.
        If the client is initialized, the function retrieves a message from the MQTT
        message queue.

        If the message payload is `None`, the function logs a warning message and continues
        to the next message. Otherwise, it decodes the payload as a UTF-8 string and logs
        the received message and topic.

        Finally, the function calls the `_handle_mqtt_msg` method to handle the received
        message.

        This function does not take any parameters and does not return any value.
        """
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
        """
        Remove any finished transient tasks from the list of transient tasks.

        This function runs in an infinite loop, sleeping for 1 second in each iteration.
        It checks for any finished tasks in the list of transient tasks and removes them.
        Once the finished tasks are removed, it gathers the results of those tasks and checks
        for any exceptions. If an exception is found, it raises the exception and logs an error
        message with the task information.

        Parameters:
            None

        Returns:
            None
        """
        while True:
            await asyncio.sleep(1)
            finished_tasks = [x for x in self.transient_tasks if x.done()]
            if not finished_tasks:
                continue
            for task in finished_tasks:
                self.transient_tasks.remove(task)
            results = await asyncio.gather(*finished_tasks, return_exceptions=True)
            for i, exception in [
                x for x in enumerate(results) if isinstance(x[1], Exception)
            ]:
                task = finished_tasks[i]
                try:
                    raise exception
                except Exception:  # pylint: disable=broad-except
                    _LOG.exception("Exception in task: %r:", task)

    async def digital_output_loop(
        self, module: GenericGPIO, queue: "asyncio.Queue[Tuple[ConfigType, str]]"
    ) -> None:
        """
        Handle digital output MQTT messages for a specific GPIO module.
        An instance of this loop will be created for each individual GPIO module so that
        when messages come in via MQTT, we don't have to wait for some other module's
        action to complete before carrying out this one.

        It may seem like we should use this loop to handle /set_on_ms and /set_off_ms
        messages, but it's actually better that we don't, since any timed stuff would
        hold up /set messages that need to take place immediately.
        """
        while True:
            out_conf, payload = await queue.get()
            if payload not in (out_conf["on_payload"], out_conf["off_payload"]):
                _LOG.warning(
                    "'%s' is not a valid payload for output %s. Only '%s' and '%s' are allowed.",
                    payload,
                    out_conf["name"],
                    out_conf["on_payload"],
                    out_conf["off_payload"],
                )
                continue

            value = payload == out_conf["on_payload"]
            await self.set_digital_output(module, out_conf, value)

            try:
                msec = out_conf["timed_set_ms"]
            except KeyError:
                continue

            async def reset_timer(out_conf: ConfigType = out_conf) -> None:
                """
                Reset the output to the opposite value after x ms.
                """
                await asyncio.sleep(msec / 1000.0)
                _LOG.info(
                    (
                        "Setting digital output '%s' back to its previous value after "
                        "configured 'timed_set_ms' delay of %sms"
                    ),
                    out_conf["name"],
                    msec,
                )
                await self.set_digital_output(module, out_conf, not value)

            task = self.loop.create_task(reset_timer())
            self.transient_tasks.append(task)

    async def stream_output_loop(
        self,
        module: GenericStream,
        stream_conf: ConfigType,
        queue: "asyncio.Queue[bytes]",
    ) -> None:
        """
        Wait for data to appear on the queue, then send it to the stream.
        """
        while True:
            data = await queue.get()
            try:
                await module.async_write(data)
            except Exception:  # pylint: disable=broad-except
                _LOG.exception(
                    "Exception while sending data to stream '%s':", stream_conf["name"]
                )
            else:
                self.event_bus.fire(StreamDataSentEvent(stream_conf["name"], data))

    async def _main_loop(self) -> None:
        """
        Asynchronous main loop function.

        This function is responsible for running the main event loop of the MQTT client.
        It handles reconnecting to the MQTT broker if the connection is lost and
        manages the execution of critical tasks.

        Parameters:
            None

        Returns:
            None
        """
        reconnect = True
        reconnect_delay = self.config["mqtt"]["reconnect_delay"]
        reconnects_remaining = None
        while reconnect:
            try:
                await self._connect_mqtt()
                # Reset reconnects remaining once successful
                reconnects_remaining = self.config["mqtt"]["reconnect_count"]
                self.critical_tasks = [
                    self.loop.create_task(coro)
                    for coro in (
                        self._mqtt_task_loop(),
                        self._mqtt_rx_loop(),
                        self._mqtt_keep_alive_loop(),
                        self._remove_finished_transient_tasks(),
                    )
                ]

                self.running.set()

                if self.config["mqtt"].get("ha_discovery", {}).get("enabled"):
                    self._ha_discovery_announce()

                await asyncio.gather(*self.critical_tasks)
            except asyncio.CancelledError:
                break
            except (MQTTException,MqttCodeError):
                if reconnects_remaining is not None:
                    reconnect = reconnects_remaining > 0
                    reconnects_remaining -= 1
                _LOG.exception("Connection to MQTT broker failed")
            except Exception:  # pylint: disable=broad-except
                _LOG.exception("Exception in critical task:")

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

        self._init_gpio_modules()
        self._init_digital_inputs()
        self._init_digital_outputs()
        self._init_sensor_modules()
        self._init_sensor_inputs()
        self._init_stream_modules()

        self._main_task = self.loop.create_task(self._main_loop())

        _LOG.debug("Going Asynchronous")
        try:
            self.loop.run_until_complete(self._main_task)
        finally:
            self.loop.close()
            _LOG.debug("Loop closed")
            for module_type in ("gpio", "sensor", "stream"):
                for module in getattr(self, f"{module_type}_modules").values():
                    _LOG.debug("Running cleanup on module %s", module)
                    try:
                        module.cleanup()
                    except Exception:  # pylint: disable=broad-except
                        _LOG.exception(
                            "Exception while cleaning up %s module %s",
                            module_type,
                            module,
                        )
        _LOG.debug("run() complete")

    async def shutdown(self) -> None:
        """
        Shut down all of the tasks involved in running the server.
        """
        # Cancel our tasks
        our_tasks: List["asyncio.Task[Any]"] = self.critical_tasks + self.transient_tasks
        for task in our_tasks:
            task.cancel()

        _LOG.info("Waiting for our tasks to complete...")
        results = await asyncio.gather(*our_tasks, return_exceptions=True)
        for i, result in enumerate(results):
            if isinstance(result, asyncio.CancelledError):
                continue
            if isinstance(result, Exception):
                _LOG.error("Task %s raised an exception: %s", results[i], result)

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
