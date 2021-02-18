"""
The main business logic of the server.

Coordinates initialisation of the GPIO, sensor and stream modules, along with getting
and setting their values and data, connecting to MQTT and sending/receiving MQTT messages.
"""

# pylint: enable=duplicate-code

from __future__ import annotations

import asyncio
import logging
import re
import signal as signals
import threading
from concurrent.futures import Future as ConcurrentFuture
from functools import partial
from hashlib import sha1
from importlib import import_module
from queue import Queue
from typing import Any, Awaitable, Dict, List, Optional, Tuple, Type, Union, overload

from hbmqtt.client import MQTTClient  # type: ignore
from hbmqtt.mqtt.constants import QOS_1  # type: ignore
from typing_extensions import Literal

from .config import (
    validate_and_normalise_config,
    validate_and_normalise_digital_input_config,
    validate_and_normalise_digital_output_config,
    validate_and_normalise_sensor_input_config,
)
from .constants import (
    INPUT_TOPIC,
    MODULE_CLASS_NAMES,
    MODULE_IMPORT_PATH,
    OUTPUT_TOPIC,
    SENSOR_TOPIC,
    SET_OFF_MS_TOPIC,
    SET_ON_MS_TOPIC,
    SET_TOPIC,
)
from .events import (
    DigitalInputChangedEvent,
    DigitalOutputChangedEvent,
    EventBus,
    SensorReadEvent,
)
from .home_assistant import (
    hass_announce_digital_input,
    hass_announce_digital_output,
    hass_announce_sensor_input,
)
from .modules import BASE_SCHEMA as MODULE_BASE_SCHEMA
from .modules import install_missing_requirements
from .modules.gpio import GenericGPIO, InterruptEdge, InterruptSupport, PinDirection
from .modules.sensor import GenericSensor
from .types import ConfigType, PinType, UnawaitedTaskType

_LOG = logging.getLogger(__name__)


@overload
def _init_module(
    module_config: Dict[str, Dict[str, Any]], module_type: Literal["gpio"]
) -> GenericGPIO:
    ...


@overload
def _init_module(
    module_config: Dict[str, Dict[str, Any]], module_type: Literal["sensor"]
) -> GenericSensor:
    ...


def _init_module(
    module_config: Dict[str, Dict[str, Any]], module_type: str
) -> Union[GenericGPIO, GenericSensor]:
    """
    Initialise a GPIO module by:
    - Importing it
    - Validating its config
    - Installing any missing requirements for it
    - Instantiating its class
    """
    module = import_module(
        "%s.%s.%s" % (MODULE_IMPORT_PATH, module_type, module_config["module"])
    )
    # Doesn't need to be a deep copy because we're not mutating the base rules
    module_schema = MODULE_BASE_SCHEMA.copy()
    # Add the module's config schema to the base schema
    module_schema.update(getattr(module, "CONFIG_SCHEMA", {}))
    module_config = validate_and_normalise_config(module_config, module_schema)
    install_missing_requirements(module)
    module_class: Union[Type[GenericGPIO], Type[GenericSensor]] = getattr(
        module, MODULE_CLASS_NAMES[module_type]
    )
    return module_class(module_config)


def output_name_from_topic(topic: str, prefix: str) -> str:
    """
    Parses an MQTT topic and returns the name of the output that the message relates to.
    """
    match = re.match("^{}/{}/(.+?)/.+$".format(prefix, OUTPUT_TOPIC), topic)
    if match is None:
        raise ValueError("Topic %r does not adhere to expected structure" % topic)
    return match.group(1)


class MqttIo:  # pylint: disable=too-many-instance-attributes
    """
    The main class that represents the business logic of the server. This is instantiated
    once per config file, of which there is generally only one.
    """

    def __init__(self, config: Dict[str, Any]) -> None:
        self.config = config
        self.gpio_configs: Dict[str, Dict[str, Any]] = {}
        self.sensor_configs: Dict[str, Dict[str, Any]] = {}
        self.digital_input_configs: Dict[str, Dict[str, Any]] = {}
        self.digital_output_configs: Dict[str, Dict[str, Any]] = {}
        self.sensor_input_configs: Dict[str, Dict[str, Any]] = {}
        self.gpio_modules: Dict[str, GenericGPIO] = {}
        self.sensor_modules: Dict[str, GenericSensor] = {}
        self.module_output_queues = (
            {}
        )  # type: Dict[str, asyncio.Queue[Tuple[GenericGPIO, Dict[str, Any], str]]]

        self.loop = asyncio.get_event_loop()
        self.tasks = []  # type: List[asyncio.Future[Any]]
        self.unawaited_tasks: List[UnawaitedTaskType] = []

        self.event_bus = EventBus(self.loop, self.unawaited_tasks)
        self.mqtt: MQTTClient = None
        self.interrupt_locks: Dict[str, threading.Lock] = {}
        self.mqtt_publish_queue = Queue()  # type: Queue[Awaitable[Any]]

    # Init methods

    def _init_gpio_modules(self) -> None:
        self.gpio_configs = {x["name"]: x for x in self.config["gpio_modules"]}
        self.gpio_modules = {}
        for gpio_config in self.config["gpio_modules"]:
            self.gpio_modules[gpio_config["name"]] = _init_module(gpio_config, "gpio")

    def _init_sensor_modules(self) -> None:
        self.sensor_configs = {x["name"]: x for x in self.config["sensor_modules"]}
        self.sensor_modules = {}
        for sens_config in self.config["sensor_modules"]:
            self.sensor_modules[sens_config["name"]] = _init_module(sens_config, "sensor")

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
            val = in_conf["on_payload"] if event.to_value else in_conf["off_payload"]
            self.mqtt_publish_queue.put(
                self.mqtt.publish(
                    "%s/%s/%s"
                    % (
                        self.config["mqtt"]["topic_prefix"],
                        INPUT_TOPIC,
                        event.input_name,
                    ),
                    val.encode("utf8"),
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
                self.unawaited_tasks.append(
                    self.loop.create_task(self.digital_input_poller(gpio_module, in_conf))
                )

            if interrupt is None:
                continue

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
                callback = partial(self.interrupt_callback, gpio_module, in_conf["pin"])
            gpio_module.setup_interrupt_internal(
                in_conf["pin"], edge, in_conf, callback=callback
            )

    def _init_digital_outputs(self) -> None:
        # Set up MQTT publish callback for output event
        async def publish_callback(event: DigitalOutputChangedEvent) -> None:
            out_conf = self.digital_output_configs[event.output_name]
            val = out_conf["on_payload"] if event.to_value else out_conf["off_payload"]
            self.mqtt_publish_queue.put(
                self.mqtt.publish(
                    "%s/output/%s"
                    % (self.config["mqtt"]["topic_prefix"], event.output_name),
                    val.encode("utf8"),
                    qos=1,
                    retain=out_conf["retain"],
                )
            )

        self.event_bus.subscribe(DigitalOutputChangedEvent, publish_callback)

        for out_conf in self.config["digital_outputs"]:
            gpio_module = self.gpio_modules[out_conf["module"]]
            out_conf = validate_and_normalise_digital_output_config(out_conf, gpio_module)
            self.digital_output_configs[out_conf["name"]] = out_conf

            gpio_module.setup_pin_internal(PinDirection.OUTPUT, out_conf)

            # Create queues for each module with an output
            if out_conf["module"] not in self.module_output_queues:
                queue = (
                    asyncio.Queue()
                )  # type: asyncio.Queue[Tuple[GenericGPIO, Dict[str, Any], str]]
                self.module_output_queues[out_conf["module"]] = queue

                # Use partial to avoid late binding closure
                self.unawaited_tasks.append(
                    self.loop.create_task(partial(self.digital_output_loop, queue)())
                )

    def _init_sensor_inputs(self) -> None:
        async def publish_sensor_callback(event: SensorReadEvent) -> None:
            self.mqtt_publish_queue.put(
                self.mqtt.publish(
                    "%s/%s/%s"
                    % (
                        self.config["mqtt"]["topic_prefix"],
                        SENSOR_TOPIC,
                        event.sensor_name,
                    ),
                    str(event.value).encode("utf8"),
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
                while True:
                    value = await sensor_module.async_get_value(sens_conf)
                    if value is not None:
                        value = round(value, sens_conf["digits"])
                        _LOG.info(
                            "Read sensor '%s' value of %s", sens_conf["name"], value
                        )
                        self.event_bus.fire(SensorReadEvent(sens_conf["name"], value))
                    await asyncio.sleep(sens_conf["interval"])

            self.unawaited_tasks.append(self.loop.create_task(poll_sensor()))

    async def _init_mqtt(self) -> None:  # pylint: disable=too-many-locals
        config: ConfigType = self.config["mqtt"]
        topic_prefix: str = config["topic_prefix"]

        client_id: Optional[str] = config["client_id"]
        if not client_id:
            client_id = "mqtt-io-%s" % sha1(topic_prefix.encode("utf8")).hexdigest()

        tls_enabled: bool = config.get("tls", {}).get("enabled")

        uri = "mqtt%s://" % ("s" if tls_enabled else "")
        if config["user"] and config["password"]:
            uri += "%s:%s@" % (config["user"], config["password"])
        uri += "%s:%s" % (config["host"], config["port"])

        client_config = dict(
            keep_alive=config["keepalive"],
        )
        connect_kwargs = dict(cleansession=config["clean_session"])
        if tls_enabled:
            tls_config = config["tls"]
            if tls_config.get("certfile") and tls_config.get("keyfile"):
                client_config.update(
                    dict(
                        certfile=tls_config.get("certfile") or None,
                        keyfile=tls_config.get("keyfile") or None,
                    )
                )
            client_config["check_hostname"] = not tls_config["insecure"]
            connect_kwargs.update(
                dict(
                    capath=tls_config.get("ca_certs"),
                    cafile=tls_config.get("ca_file"),
                    cadata=tls_config.get("ca_data"),
                )
            )
        client_config["will"] = dict(
            retain=True,
            topic="%s/%s" % (topic_prefix, config["status_topic"]),
            message=config["status_payload_dead"].encode("utf8"),
            qos=1,
        )

        self.mqtt = MQTTClient(client_id=client_id, config=client_config, loop=self.loop)
        _LOG.info("Connecting to MQTT...")
        await self.mqtt.connect(uri, **connect_kwargs)
        _LOG.info("Connected to MQTT")
        for out_conf in self.digital_output_configs.values():
            for suffix in (SET_TOPIC, SET_ON_MS_TOPIC, SET_OFF_MS_TOPIC):
                topic = "%s/%s/%s/%s" % (
                    topic_prefix,
                    OUTPUT_TOPIC,
                    out_conf["name"],
                    suffix,
                )
                await self.mqtt.subscribe([(topic, QOS_1)])
                _LOG.info("Subscribed to topic: %r", topic)

        await self.mqtt.publish(
            "%s/%s" % (topic_prefix, config["status_topic"]),
            config["status_payload_running"].encode("utf8"),
            qos=1,
            retain=True,
        )

        # Publish initial values of outputs if desired
        for out_conf in self.digital_output_configs.values():
            if not out_conf["publish_initial"]:
                continue
            value = out_conf["initial"] == "high"
            payload = (
                out_conf["on_payload"]
                if value != out_conf["inverted"]
                else out_conf["off_payload"]
            )
            await self.mqtt.publish(
                "%s/output/%s" % (topic_prefix, out_conf["name"]),
                payload.encode("utf8"),
                qos=1,
                retain=out_conf["retain"],
            )
        # Publish Home Assistant Discovery messages if desired
        if config["discovery"]:
            for in_conf in self.digital_input_configs.values():
                await hass_announce_digital_input(in_conf, config, self.mqtt)
            for out_conf in self.digital_output_configs.values():
                await hass_announce_digital_output(out_conf, config, self.mqtt)
            for sens_conf in self.sensor_configs.values():
                await hass_announce_sensor_input(sens_conf, config, self.mqtt)

    # Runtime methods

    async def digital_input_poller(
        self, module: GenericGPIO, in_conf: Dict[str, Any]
    ) -> None:
        """
        Polls a single digital input for changes and fires a DigitalInputchangedEvent
        when it changes.

        This function also helps maintain the working state of pins which are configured
        as interrupts for other pins by checking if it's in the 'triggered' state. This
        could mean that the interrupt callback code didn't fire when the pin changed
        state. If that happens, you can end up in a deadlock where the pin remains in that
        state until the remote interrupt is 'handled', which would be never, unless this
        loop polls the 'triggered' value and calls the interupt handling code itself.

        If the interrupt lock is not acquired, then it means that the interrupt is already
        being handled, so we can check again on the next poll.
        """
        last_value = None
        while True:
            value = await module.async_get_pin(in_conf["pin"])
            if value != last_value:
                _LOG.info(
                    "Digital input '%s' value changed to %s", in_conf["name"], value
                )
                self.event_bus.fire(
                    DigitalInputChangedEvent(in_conf["name"], last_value, value)
                )
                last_value = value
            # If the value is now the same as the 'interrupt' value (falling, rising)
            # and we're a remote interrupt then just trigger the remote interrupt
            interrupt = in_conf.get("interrupt")
            interrupt_for = in_conf.get("interrupt_for")
            if not interrupt or not interrupt_for:
                continue
            if not any(
                (
                    interrupt == "rising" and value,
                    interrupt == "falling" and not value,
                    # Doesn't work for 'both' because there's no one 'triggered' state
                    # to check if we're stuck in.
                    # interrupt == "both",
                )
            ):
                continue
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
                continue
            _LOG.debug(
                "Polled value of %s on '%s' triggered remote interrupt",
                value,
                in_conf["name"],
            )
            self.handle_remote_interrupt(interrupt_for, interrupt_lock)
            await asyncio.sleep(in_conf["poll_interval"])

    def interrupt_callback(
        self,
        module: GenericGPIO,
        pin: PinType,
        *args: List[Any],
        **kwargs: Dict[Any, Any]
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
        """
        pin_name = module.pin_configs[pin]["name"]
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

        task = asyncio.run_coroutine_threadsafe(await_remote_interrupts(), self.loop)
        self.unawaited_tasks.append(task)

    def _handle_mqtt_msg(self, topic: str, payload: str) -> None:
        """
        Parse all MQTT messages received on our subscriptions and dispatch actions
        such as changing outputs and sending data to streams accordingly.
        """
        topic_prefix: str = self.config["mqtt"]["topic_prefix"]

        if not any(
            topic.endswith("/%s" % x)
            for x in (SET_TOPIC, SET_ON_MS_TOPIC, SET_OFF_MS_TOPIC)
        ):
            _LOG.debug(
                "Ignoring message to topic '%s' which doesn't end with '/set' etc.", topic
            )
            return
        try:
            output_name = output_name_from_topic(topic, topic_prefix)
        except ValueError as exc:
            _LOG.warning("Unable to parse topic: %s", exc)
            return
        output_config = self.digital_output_configs[output_name]
        module = self.gpio_modules[output_config["module"]]
        if topic.endswith("/%s" % SET_TOPIC):
            # This is a message to set a digital output to a given value
            self.module_output_queues[output_config["module"]].put_nowait(
                (module, output_config, payload)
            )
        else:
            # This must be a set_on_ms or set_off_ms topic
            desired_value = topic.endswith("/%s" % SET_ON_MS_TOPIC)

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
                    output_config["name"],
                    "on" if desired_value else "off",
                    secs,
                )
                await self.set_digital_output(module, output_config, desired_value)
                await asyncio.sleep(secs)
                _LOG.info(
                    "Turning output '%s' %s after %s second(s) elapsed",
                    output_config["name"],
                    "off" if desired_value else "on",
                    secs,
                )
                await self.set_digital_output(module, output_config, not desired_value)

            task = self.loop.create_task(set_ms())
            self.unawaited_tasks.append(task)

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

    async def _mqtt_tx_loop(self) -> None:
        """
        Use a task to publish MQTT messages from a queue so that we don't try to publish
        them before MQTT is initialised.
        """
        while True:
            try:
                await self.mqtt_publish_queue.get()
            except Exception:  # pylint: disable=broad-except
                _LOG.exception("Unable to publish MQTT message:")

    async def _mqtt_rx_loop(self) -> None:
        try:
            while True:
                msg = await self.mqtt.deliver_message()
                topic = msg.publish_packet.variable_header.topic_name
                payload = msg.publish_packet.payload.data.decode("utf8")
                _LOG.info("Received message on topic %r: %r", topic, payload)
                self._handle_mqtt_msg(topic, payload)
        finally:
            await self.mqtt.publish(
                "%s/%s"
                % (
                    self.config["mqtt"]["topic_prefix"],
                    self.config["mqtt"]["status_topic"],
                ),
                self.config["mqtt"]["status_payload_stopped"].encode("utf8"),
                qos=1,
                retain=True,
            )
            _LOG.info("Disconnecting from MQTT...")
            await self.mqtt.disconnect()
            _LOG.info("MQTT disconnected")

    async def _remove_finished_tasks(self) -> None:
        while True:
            await asyncio.sleep(1)
            finished_tasks = [x for x in self.unawaited_tasks if x.done()]
            if not finished_tasks:
                continue
            for task in finished_tasks:
                if isinstance(task, ConcurrentFuture):
                    # task = self.loop.run_in_executor(ThreadPoolExecutor(), task)
                    task = asyncio.wrap_future(task)
                try:
                    await task
                except Exception:  # pylint: disable=broad-except
                    _LOG.exception("Exception in task: %r:", task)
            self.unawaited_tasks = list(
                filter(lambda x: not x.done(), self.unawaited_tasks)
            )

    async def digital_output_loop(
        self, queue: "asyncio.Queue[Tuple[GenericGPIO, Dict[str, Any], str]]"
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
            module, output_config, payload = await queue.get()
            if payload not in (output_config["on_payload"], output_config["off_payload"]):
                _LOG.warning(
                    "'%s' is not a valid payload for output %s. Only '%s' and '%s' are allowed.",
                    payload,
                    output_config["name"],
                    output_config["on_payload"],
                    output_config["off_payload"],
                )
                continue

            value = payload == output_config["on_payload"]
            await self.set_digital_output(module, output_config, value)

            try:
                msec = output_config["timed_set_ms"]
            except KeyError:
                continue

            async def reset_timer() -> None:
                """
                Reset the output to the opposite value after x ms.
                """
                await asyncio.sleep(msec / 1000.0)
                _LOG.info(
                    (
                        "Setting digital output '%s' back to its previous value after "
                        "configured 'timed_set_ms' delay of %sms"
                    ),
                    output_config["name"],
                    msec,
                )
                await self.set_digital_output(module, output_config, not value)

            task = self.loop.create_task(reset_timer())
            self.unawaited_tasks.append(task)

    # Main entry point

    def run(self) -> None:
        """
        Main entry point into the server which initialises all of the modules, connects to
        MQTT and starts the event loop.
        """
        for sig in (signals.SIGHUP, signals.SIGTERM, signals.SIGINT):
            self.loop.add_signal_handler(
                sig, lambda sig=sig: self.loop.create_task(self.shutdown(sig))
            )

        # Initialise the modules and IOs
        self._init_gpio_modules()
        self._init_digital_inputs()
        self._init_digital_outputs()
        self._init_sensor_modules()
        self._init_sensor_inputs()

        # Get connected to the MQTT server
        self.loop.run_until_complete(self._init_mqtt())

        # This is where we add any other async tasks that we want to run, such as polling
        # inputs, sensor loops etc.
        self.tasks = [
            self.loop.create_task(coro)
            for coro in (
                self._mqtt_tx_loop(),
                self._mqtt_rx_loop(),
                self._remove_finished_tasks(),
            )
        ]
        try:
            self.loop.run_forever()
        finally:
            self.loop.close()
            _LOG.debug("Loop closed")
            for gpio_module in self.gpio_modules.values():
                try:
                    gpio_module.cleanup()
                except Exception:  # pylint: disable=broad-except
                    _LOG.exception(
                        "Exception while cleaning up gpio module %s", gpio_module
                    )
            for sens_module in self.sensor_modules.values():
                try:
                    sens_module.cleanup()
                except Exception:  # pylint: disable=broad-except
                    _LOG.exception(
                        "Exception while cleaning up sensor module %s", sens_module
                    )
        _LOG.debug("run() complete")

    async def shutdown(self, signal: "signals.Signals") -> None:
        """
        Shut down all of the tasks involved in running the server in the right order.
        """
        _LOG.warning("Received exit signal %s", signal.name)

        # Cancel our main task first so we don't mess the MQTT library's connection
        for task in self.tasks:
            task.cancel()
        _LOG.info("Waiting for main task to complete...")
        all_done = False
        while not all_done:
            all_done = all(t.done() for t in self.tasks)
            await asyncio.sleep(0.1)

        current_task = asyncio.Task.current_task()
        tasks = [
            t
            for t in asyncio.Task.all_tasks(loop=self.loop)
            if not t.done() and t is not current_task
        ]
        _LOG.info("Cancelling %s remaining tasks", len(tasks))
        for task in tasks:
            task.cancel()
        _LOG.info("Waiting for %s remaining tasks to complete...", len(tasks))
        all_done = False
        while not all_done:
            all_done = all(t.done() for t in tasks)
            await asyncio.sleep(0.1)
        _LOG.debug("Tasks all finished. Stopping loop...")
        self.loop.stop()
        _LOG.debug("Loop stopped")
        unsent_messages = self.mqtt_publish_queue.qsize()
        if unsent_messages:
            _LOG.warning("%s queued MQTT message(s) not sent", unsent_messages)
