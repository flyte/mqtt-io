"""
Provides "GPIO" which handles reading, writing and interrupts for GPIO pins.
"""
import logging
import threading
from functools import partial
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

import trio
from trio_typing import TaskStatus

from .abc import GenericIO
from .config import (
    validate_and_normalise_digital_input_config,
    validate_and_normalise_digital_output_config,
)
from .constants import (
    INPUT_TOPIC,
    OUTPUT_TOPIC,
    SET_OFF_MS_SUFFIX,
    SET_ON_MS_SUFFIX,
    SET_SUFFIX,
)
from .events import DigitalInputChangedEvent, DigitalOutputChangedEvent
from .helpers import _init_module, output_name_from_topic
from .modules.gpio import GenericGPIO, InterruptEdge, InterruptSupport, PinDirection
from .types import ConfigType, PinType
from .utils import hold_channel_open

if TYPE_CHECKING:
    # pylint: disable=cyclic-import
    from .server_trio import MQTTIO
_LOG = logging.getLogger(__name__)


# pylint: enable=duplicate-code
# pylint: disable=too-many-lines


class GPIO(GenericIO):  # pylint: disable=too-many-instance-attributes
    """
    Handles GPIO-Modules
    """

    def __init__(self, config: ConfigType, server: "MQTTIO") -> None:
        self.config = config
        self.server = server

        self.gpio_configs: Dict[str, ConfigType] = {}
        self.digital_input_configs: Dict[str, ConfigType] = {}
        self.digital_output_configs: Dict[str, ConfigType] = {}
        self.gpio_modules: Dict[str, GenericGPIO] = {}

        self.gpio_output_channels: Dict[
            str, Tuple[trio.MemorySendChannel, trio.MemoryReceiveChannel]
        ] = {}

        self.interrupt_locks: Dict[str, threading.Lock] = {}

    async def init(self) -> None:
        """
        Initializes modules, inputs and outputs.
        """
        await self.init_gpio_modules()
        await self.init_digital_inputs()
        await self.init_digital_outputs()

    async def init_gpio_modules(self) -> None:
        """
        Initialise GPIO modules.
        """
        self.gpio_configs = {x["name"]: x for x in self.config["gpio_modules"]}
        self.gpio_modules = {}
        for gpio_config in self.config["gpio_modules"]:
            self.gpio_modules[gpio_config["name"]] = await _init_module(
                gpio_config, "gpio", self.config["options"]["install_requirements"]
            )

    def _publish_io(
        self, name: str, value: str, in_out_topic: str, qos: int = 1, retain: bool = False
    ) -> None:
        self.server.mqtt.publish(
            "/".join((self.server.config["mqtt"]["topic_prefix"], in_out_topic, name)),
            value.encode("utf8"),
            qos=qos,
            retain=retain,
        )

    async def init_digital_inputs(self) -> None:
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

        async def publish_input_changes(
            event_rx: trio.MemoryReceiveChannel,
            task_status: TaskStatus[None] = trio.TASK_STATUS_IGNORED,
        ) -> None:
            event: DigitalInputChangedEvent
            async with event_rx:
                task_status.started()
                async for event in event_rx:
                    in_conf = self.digital_input_configs[event.input_name]
                    value = event.to_value != in_conf["inverted"]
                    val = in_conf["on_payload"] if value else in_conf["off_payload"]
                    self._publish_io(
                        event.input_name, val, INPUT_TOPIC, retain=in_conf["retain"]
                    )

        event_rx = await self.server.event_bus.subscribe(DigitalInputChangedEvent)
        await self.server.nursery.start(publish_input_changes, event_rx)

        for in_conf in self.config["digital_inputs"]:
            gpio_module = self.gpio_modules[in_conf["module"]]
            in_conf = validate_and_normalise_digital_input_config(in_conf, gpio_module)
            self.digital_input_configs[in_conf["name"]] = in_conf

            await trio.to_thread.run_sync(
                gpio_module.setup_pin_internal, PinDirection.INPUT, in_conf
            )

            interrupt = in_conf.get("interrupt")
            interrupt_for = in_conf.get("interrupt_for")

            # Only start the poller task if this _isn't_ set up with an interrupt, or if
            # it _is_ an interrupt, but it's used for triggering remote interrupts.
            if interrupt is None or (
                interrupt_for and in_conf["poll_when_interrupt_for"]
            ):
                self.server.nursery.start_soon(
                    self.digital_input_poller, gpio_module, in_conf
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
                await trio.to_thread.run_sync(
                    gpio_module.setup_interrupt_internal,
                    in_conf["pin"],
                    edge,
                    in_conf,
                    callback,
                )

    async def init_digital_outputs(self) -> None:
        """
        Initializes all outputs.
        """

        async def publish_digital_outputs(
            event_rx: trio.MemoryReceiveChannel,
            task_status: TaskStatus[None] = trio.TASK_STATUS_IGNORED,
        ) -> None:
            event: DigitalOutputChangedEvent
            async with event_rx:
                task_status.started()
                async for event in event_rx:
                    out_conf = self.digital_output_configs[event.output_name]
                    val = (
                        out_conf["on_payload"]
                        if event.to_value
                        else out_conf["off_payload"]
                    )
                    self._publish_io(
                        event.output_name, val, OUTPUT_TOPIC, retain=out_conf["retain"]
                    )

        event_rx = await self.server.event_bus.subscribe(DigitalOutputChangedEvent)
        await self.server.nursery.start(publish_digital_outputs, event_rx)

        for out_conf in self.config["digital_outputs"]:
            gpio_module = self.gpio_modules[out_conf["module"]]
            out_conf = validate_and_normalise_digital_output_config(out_conf, gpio_module)
            self.digital_output_configs[out_conf["name"]] = out_conf

            await trio.to_thread.run_sync(
                gpio_module.setup_pin_internal, PinDirection.OUTPUT, out_conf
            )

            # Create channels for each module with an output
            if out_conf["module"] not in self.gpio_output_channels:
                tx_chan, rx_chan = trio.open_memory_channel(0)
                self.gpio_output_channels[out_conf["module"]] = (tx_chan, rx_chan)
                await self.server.nursery.start(hold_channel_open, tx_chan)

                self.server.nursery.start_soon(
                    self.digital_output_loop,
                    gpio_module,
                    rx_chan,
                )

            for suffix in (SET_SUFFIX, SET_ON_MS_SUFFIX, SET_OFF_MS_SUFFIX):
                self.server.mqtt.subscribe(
                    "/".join(
                        (
                            self.config["mqtt"]["topic_prefix"],
                            OUTPUT_TOPIC,
                            out_conf["name"],
                            suffix,
                        )
                    )
                )

            # Fire DigitalOutputChangedEvents for initial values of outputs if required
            if out_conf["publish_initial"]:
                self.server.event_bus.fire(
                    DigitalOutputChangedEvent(
                        out_conf["name"],
                        out_conf["initial"]
                        == ("low" if out_conf["inverted"] else "high"),
                    )
                )

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
            self.server.event_bus.fire(
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
            await trio.sleep(in_conf["poll_interval"])

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
            self.server.event_bus.fire(DigitalInputChangedEvent(pin_name, None, value))
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
                    self.server.event_bus.fire(
                        DigitalInputChangedEvent(remote_pin_name, None, value)
                    )

            remote_interrupt_tasks.append(partial(handle_remote_interrupt_task)())

        async def await_remote_interrupts() -> None:
            """
            Await all of the remote interrupt tasks so that we can release the interrupt
            lock afterwards.
            """
            try:
                async with trio.open_nursery() as nursery:
                    for coro_func in remote_interrupt_tasks:
                        nursery.start_soon(coro_func)
            finally:
                interrupt_lock.release()

        trio.from_thread.run_sync(
            self.server.nursery.start_soon,
            await_remote_interrupts,
            trio_token=self.server.trio_token,
        )

    async def handle_mqtt_msg(self, topic: str, payload: bytes) -> None:
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
            await self.handle_digital_output_msg(topic, payload_str)

    async def handle_digital_output_msg(self, topic: str, payload: str) -> None:
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
            tx_chan, _ = self.gpio_output_channels[out_conf["module"]]
            try:
                tx_chan.send_nowait((out_conf, payload))
            except trio.WouldBlock:
                _LOG.error(
                    "'%s' module output channel full when handling digital output msg",
                    module,
                )
        else:
            # This must be a set_on_ms or set_off_ms topic
            desired_value = topic.endswith("/%s" % SET_ON_MS_SUFFIX)

            async def set_ms(
                task_status: TaskStatus[None] = trio.TASK_STATUS_IGNORED,
            ) -> None:
                """
                Create this task to directly set the outputs, as we don't want to tie up
                the set_digital_output loop. Creating a bespoke task for the job is the
                simplest and most effective way of leveraging the asyncio framework.
                """
                task_status.started()
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
                await trio.sleep(secs)
                _LOG.info(
                    "Turning output '%s' %s after %s second(s) elapsed",
                    out_conf["name"],
                    "off" if desired_value else "on",
                    secs,
                )
                await self.set_digital_output(module, out_conf, not desired_value)

            # Timing sensitive task, so start it right away
            await self.server.nursery.start(set_ms)

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
        self.server.event_bus.fire(
            DigitalOutputChangedEvent(output_config["name"], value)
        )

    async def digital_output_loop(
        self, module: GenericGPIO, rx_chan: trio.MemoryReceiveChannel
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
        output_action: Tuple[ConfigType, str]
        async for output_action in rx_chan:
            out_conf, payload = output_action
            if payload not in (out_conf["on_payload"], out_conf["off_payload"]):
                _LOG.warning(
                    "'%s' is not a valid payload for output %s. Only '%s' and '%s' are allowed.",
                    payload,
                    out_conf["name"],
                    out_conf["on_payload"],
                    out_conf["off_payload"],
                )
                continue

            value: bool = payload == out_conf["on_payload"]
            await self.set_digital_output(module, out_conf, value)

            if "timed_set_ms" not in out_conf:
                continue

            async def reset_timer(
                out_conf: ConfigType = out_conf,
                value: bool = value,
                task_status: TaskStatus[None] = trio.TASK_STATUS_IGNORED,
            ) -> None:
                """
                Reset the output to the opposite value after x ms.
                """
                task_status.started()
                msec: int = out_conf["timed_set_ms"]
                await trio.sleep(msec / 1000.0)
                _LOG.info(
                    (
                        "Setting digital output '%s' back to its previous value after "
                        "configured 'timed_set_ms' delay of %sms"
                    ),
                    out_conf["name"],
                    msec,
                )
                await self.set_digital_output(module, out_conf, not value)

            # Timing sensitive task, so start it right away
            await self.server.nursery.start(reset_timer)

    def cleanup(self) -> None:
        """
        Cleans up all modules
        """
        for module in self.gpio_modules.values():
            _LOG.debug("Running cleanup on module %s", module)
            try:
                module.cleanup()
            except Exception:  # pylint: disable=broad-except
                _LOG.exception(
                    "Exception while cleaning up GPIO module %s",
                    module,
                )
