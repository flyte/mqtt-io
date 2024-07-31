"""
Contains the base class and some enums that are shared across all GPIO modules.
"""

# IDEA: Possible implementations -@flyte at 23/02/2021, 21:37:43
# Decide which executor we should use for async functions.
# https://docs.python.org/3/library/asyncio-eventloop.html#asyncio.loop.run_in_executor
# Should we use the default executor, or have one per module?

import abc
import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from enum import Enum, Flag, IntFlag, auto
from typing import Any, Callable, Dict, Iterable, List, Optional

from ...types import ConfigType, PinType

_LOG = logging.getLogger(__name__)


class PinDirection(Enum):
    """
    Whether the GPIO pin is an input or an output.
    """

    INPUT = auto()
    OUTPUT = auto()


class PinPUD(Enum):
    """
    Whether the GPIO pin should be pulled up, down or not anywhere.
    """

    OFF = auto()
    UP = auto()
    DOWN = auto()


class InterruptEdge(Enum):
    """
    Whether to trigger an interrupt on rising edge, falling edge or both.
    """

    RISING = auto()
    FALLING = auto()
    BOTH = auto()


class InterruptSupport(IntFlag):
    """
    Classifies the kind of support a GPIO module has for interrupts.

    These are designed to be added to the GPIO module's `INTERRUPT_SUPPORT` class constant
    by ORing them together, for example:

    class GPIO(GenericGPIO):
        INTERRUPT_SUPPORT = (
            InterruptSupport.FLAG_REGISTER | InterruptSupport.CAPTURE_REGISTER
        )

    The `INTERRUPT_SUPPORT` constant will then be used when deciding how to handle
    interrupt triggered by, or for this GPIO module.
    """

    NONE = auto()

    # The library supporting this chip provides a function callback mechanism on interrupt
    SOFTWARE_CALLBACK = auto()

    # The chip flags which pin triggered the interrupt
    FLAG_REGISTER = auto()

    # The chip captures pin values at the moment of interrupt, so
    # we can read those to return the value that the pin changed to.
    CAPTURE_REGISTER = auto()

    # The chip changes the logic level on one or more dedicated
    # interrupt pins when one of its GPIO pin's logic level changes.
    INTERRUPT_PIN = auto()

    # The chip allows you to set which pins trigger interrupts
    SET_TRIGGERS = auto()


class GenericGPIO(abc.ABC):  # pylint: disable=too-many-instance-attributes
    """
    Abstracts a generic GPIO interface to be implemented by the modules in this
    directory.
    """

    INTERRUPT_SUPPORT = InterruptSupport.NONE

    def __init__(self, config: ConfigType):
        self.config = config
        self.pin_configs: Dict[PinType, ConfigType] = {}
        self.io: Any = None  # pylint: disable=invalid-name
        self.interrupt_edges: Dict[PinType, InterruptEdge] = {}

        self.direction_map: Dict[PinDirection, Any] = {}
        self.pullup_map: Dict[PinPUD, Any] = {}
        self.interrupt_edge_map: Dict[InterruptEdge, Any] = {}

        self.executor = ThreadPoolExecutor()
        self.setup_module()

    @abc.abstractmethod
    def setup_module(self) -> None:
        """
        Called on initialisation of the GPIO module during the startup phase.

        The module's config from the `gpio_modules` section of the config file is stored
        in `self.config`.
        """

    @abc.abstractmethod
    def setup_pin(
        self,
        pin: PinType,
        direction: PinDirection,
        pullup: PinPUD,
        pin_config: ConfigType,
        initial: Optional[str] = None,
    ) -> None:
        """
        Called on initialisation of each pin of the GPIO module during the startup phase.

        The `pin_config` passed in here is the pin's entry in the `digital_inputs` or
        `digital_outputs` section of the config file.
        """

    @abc.abstractmethod
    def set_pin(self, pin: PinType, value: bool) -> None:
        """
        Set an individual pin to the given value.
        """

    @abc.abstractmethod
    def get_pin(self, pin: PinType) -> bool:
        """
        Poll a pin for its value.
        """

    def setup_interrupt(
        self,
        pin: PinType,
        edge: InterruptEdge,
        in_conf: ConfigType,
    ) -> None:
        """
        Configure a pin as an interrupt.

        This is used on modules which don't supply software callbacks, but use some other
        way of representing interrupts, such as connecting a dedicated interrupt output
        pin to another module that does supply software callbacks.
        """

    def setup_interrupt_callback(
        self,
        pin: PinType,
        edge: InterruptEdge,
        in_conf: ConfigType,
        callback: Callable[..., None],
    ) -> None:
        """
        Configure a pin as an interrupt and set up the callback function to be called when
        the interrupt is triggered.
        """

    def setup_interrupt_internal(
        self,
        pin: PinType,
        edge: InterruptEdge,
        in_conf: ConfigType,
        callback: Optional[Callable[[List[Any], Dict[Any, Any]], None]] = None,
    ) -> None:
        """
        Used internally to ensure that `self.interrupt_edges` is updated for this pin.
        """
        self.interrupt_edges[pin] = edge
        if callback is None:
            return self.setup_interrupt(pin, edge, in_conf)
        return self.setup_interrupt_callback(pin, edge, in_conf, callback)

    def cleanup(self) -> None:
        """
        Called when closing the program to handle any cleanup operations.
        """

    def setup_pin_internal(self, direction: PinDirection, pin_config: ConfigType) -> None:
        """
        Called internally to setup a pin just by supplying config. Calls setup_pin()
        that's been implemented by the GPIO module.
        """
        pin: PinType = pin_config["pin"]
        self.pin_configs[pin] = pin_config
        pud = PinPUD.OFF
        if pin_config.get("pullup"):
            pud = PinPUD.UP
        elif pin_config.get("pulldown"):
            pud = PinPUD.DOWN
        for key in ("direction", "pullup", "pulldown"):
            try:
                del pin_config[key]
            except KeyError:
                continue
        return self.setup_pin(
            pin, direction, pud, pin_config=pin_config, initial=pin_config.get("initial")
        )

    def remote_interrupt_for(self, pin: PinType) -> List[str]:
        """
        Return the list of pin names that this pin is a remote interrupt for.
        """
        return self.pin_configs[pin].get("interrupt_for", [])

    def get_int_pins(self) -> List[PinType]:
        """
        If the chip has a register that logs which pins caused the last interrupt,
        then we read it here and return the list of pins.
        """
        raise NotImplementedError()

    async def async_get_int_pins(self) -> List[PinType]:
        """
        Use a ThreadPoolExecutor to call the module's synchronous set_pin function.
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, self.get_int_pins)

    def get_captured_int_pin_values(
        self, pins: Optional[Iterable[PinType]] = None
    ) -> Dict[PinType, bool]:
        """
        If the chip has a register that logs the values of the pins at the point of
        the last interrupt, then we read it here and return a dict.

        If pins is None, then we get the whole register and return it, otherwise
        just return the values for the pins requested.
        """
        raise NotImplementedError()

    async def async_get_captured_int_pin_values(
        self, pins: Optional[Iterable[PinType]] = None
    ) -> Dict[PinType, bool]:
        """
        Use a ThreadPoolExecutor to call the module's synchronous
        get_captured_int_pin_values function.
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor, self.get_captured_int_pin_values, pins
        )

    async def async_set_pin(self, pin: PinType, value: bool) -> None:
        """
        Use a ThreadPoolExecutor to call the module's synchronous set_pin function.
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, self.set_pin, pin, value)

    async def async_get_pin(self, pin: PinType) -> bool:
        """
        Use a ThreadPoolExecutor to call the module's synchronous get_pin function.
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, self.get_pin, pin)

    def get_interrupt_value(self, pin: PinType, *args: Any, **kwargs: Any) -> bool:
        """
        Called on interrupt when this module's software callback was called, in order to
        get a value for the pin that caused the interrupt. This could just involve polling
        for the value, or looking it up in a register that captures the value at time of
        interrupt.
        """

    async def get_interrupt_values_remote(
        self, pins: List[PinType]
    ) -> Dict[PinType, bool]:
        """
        Called when another module's input pin was triggered by our module's interrupt
        pin's output changing. Takes a list of pins that can potentially trigger this
        interrupt, as defined in the `interrupt_for` list in the config file.
        """
        pins_set = set(pins)
        if self.INTERRUPT_SUPPORT & InterruptSupport.FLAG_REGISTER:
            int_pins = set(await self.async_get_int_pins())
            matching_pins = pins_set.intersection(int_pins)
            if not matching_pins:
                _LOG.warning(
                    (
                        "An interrupt was triggered for %s but none of the interrupting "
                        "pins returned by the GPIO device (%s) matched the pins "
                        "configured in `interrupt_for` (%s)."
                    ),
                    self,
                    int_pins,
                    pins,
                )
                return {}
        else:
            matching_pins = pins_set

        pin_values: Dict[PinType, bool]
        if self.INTERRUPT_SUPPORT & InterruptSupport.CAPTURE_REGISTER:
            pin_values = await self.async_get_captured_int_pin_values(pins=matching_pins)
        else:
            pin_values = {}
            for pin in matching_pins:
                try:
                    edge = self.interrupt_edges[pin]
                except KeyError:
                    _LOG.error(
                        (
                            "Pin %s on %s did not have an entry in the `interrupt_edges` "
                            "dict. This means that the pin probably wasn't configured "
                            "with an `interrupt` value in its config."
                        ),
                        pin,
                        self,
                    )
                    continue
                if edge == InterruptEdge.BOTH:
                    # We'll have to poll the pin for its current value
                    pin_values[pin] = await self.async_get_pin(pin)
                else:
                    # NOTE: Needs discussion or investigation -@flyte at 18/02/2021, 10:37:20
                    # This might cause false interrupts on chips where there's multiple
                    # pins configured as interrupts on a single remote interrupt line.
                    # If pin 0 changes value but pin 1 doesn't, and the chip doesn't
                    # provide a flag register, then this might just report that pin 1
                    # changed to its interrupt state (high or low for rising and falling
                    # respectively) when it did not, and it was just pin 0 that changed.
                    #
                    # It's probably best to make this configurable, because the
                    # alternative is just to poll the pin every time, but that could cause
                    # interrupts to report wrong values for the pin if we poll it after
                    # it's changed back to the opposite logic level. :thinking:

                    # We can infer the value based on how it's configured
                    pin_values[pin] = edge == InterruptEdge.RISING

        return pin_values
