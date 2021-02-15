import abc
import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from enum import Enum, Flag, auto
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Union

_LOG = logging.getLogger(__name__)


PinType = Union[str, int]


class PinDirection(Enum):
    INPUT = auto()
    OUTPUT = auto()


class PinPUD(Enum):
    OFF = auto()
    UP = auto()
    DOWN = auto()


class InterruptEdge(Enum):
    RISING = 0
    FALLING = 1
    BOTH = 2


class InterruptSupport(Flag):
    NONE = auto()

    # The library supporting this chip provides a callback mechanism on interrupt
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


class GenericGPIO:
    """
    Abstracts a generic GPIO interface to be implemented by the modules in this
    directory.
    """

    __metaclass__ = abc.ABCMeta

    INTERRUPT_SUPPORT = InterruptSupport.NONE

    def __init__(self, config):
        self.config = config
        self.pin_configs = {}
        self.io = None
        self.interrupt_edges = {}
        self.setup_module()

    def __init_subclass__(cls):
        cls.setup_pin = GenericGPIO._setup_pin_wrapper(cls.setup_pin)

    @abc.abstractmethod
    def setup_module(self):
        pass

    @abc.abstractmethod
    def setup_pin(
        self,
        pin: PinType,
        direction: PinDirection,
        pullup: Optional[PinPUD] = None,
        **pin_config: Dict[str, Any]
    ):
        pass

    @abc.abstractmethod
    def set_pin(self, pin, value):
        pass

    @abc.abstractmethod
    def get_pin(self, pin):
        pass

    def setup_interrupt(
        self,
        pin: PinType,
        edge: InterruptEdge,
        in_conf: Dict[str, Any],
        callback: Optional[Callable[[List[Any], Dict[Any, Any]], None]] = None,
    ):
        pass

    def cleanup(self):
        """
        Called when closing the program to handle any cleanup operations.
        """
        pass

    def setup_pin_internal(self, direction: PinDirection, pin_config: Dict[str, Any]):
        """
        Called internally to setup a pin just by supplying config. Calls setup_pin()
        that's been implemented by the GPIO module.
        """
        self.pin_configs[pin_config["pin"]] = pin_config
        pud = None
        if pin_config.get("pullup"):
            pud = PinPUD.UP
        elif pin_config.get("pulldown"):
            pud = PinPUD.DOWN
        for key in ("direction", "pullup", "pulldown"):
            try:
                del pin_config[key]
            except KeyError:
                continue
        return self.setup_pin(direction=direction, pullup=pud, **pin_config)

    def remote_interrupt_for(self, pin):
        """
        Return the list of pin names that this pin is a remote interrupt for.
        """
        return self.pin_configs[pin].get("interrupt_for", [])

    def get_int_pins(self):
        """
        If the chip has a register that logs which pins caused the last interrupt,
        then we read it here and return the list of pins.
        """
        raise NotImplementedError()

    async def async_get_int_pins(self):
        """
        Use a ThreadPoolExecutor to call the module's synchronous set_pin function.
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(ThreadPoolExecutor(), self.get_int_pins)

    def get_captured_int_pin_values(self, pins=None):
        """
        If the chip has a register that logs the values of the pins at the point of
        the last interrupt, then we read it here and return a dict.

        If pins is None, then we get the whole register and return it, otherwise
        just return the values for the pins requested.
        """
        raise NotImplementedError()

    async def async_set_pin(self, pin, value):
        """
        Use a ThreadPoolExecutor to call the module's synchronous set_pin function.
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(ThreadPoolExecutor(), self.set_pin, pin, value)

    async def async_get_pin(self, pin):
        """
        Use a ThreadPoolExecutor to call the module's synchronous get_pin function.
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(ThreadPoolExecutor(), self.get_pin, pin)

    async def get_interrupt_values_remote(self, pins):
        """
        Called when another module's input pin was triggered by our module's interrupt
        pin's output changing. Takes a list of pins that can potentially trigger this
        interrupt, as defined in the `interrupt_for` list in the config file.
        """
        # TODO: Tasks pending completion -@flyte at 27/01/2021, 18:48:22
        # Make sure that validation sets the `interrupt_for` list as minimum 1 value
        pins = set(pins)
        if self.INTERRUPT_SUPPORT & InterruptSupport.FLAG_REGISTER:
            int_pins = set(await self.async_get_int_pins())
            matching_pins = pins.intersection(int_pins)
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
            matching_pins = pins

        if self.INTERRUPT_SUPPORT & InterruptSupport.CAPTURE_REGISTER:
            pin_values = await self.get_captured_int_pin_values(pins=matching_pins)
        else:
            pin_values = {}
            for pin in matching_pins:
                try:
                    # TODO: Tasks pending completion -@flyte at 27/01/2021, 18:30:20
                    # Make sure interrupt_edges is added when setup_interrupt() is called
                    edge = self.interrupt_edges[pin]
                except KeyError:
                    # TODO: Tasks pending completion -@flyte at 27/01/2021, 18:17:52
                    # During config validation, check that any pins listed in
                    # `interrupt_for` have values for the `interrupt` setting on their
                    # `digital_inputs` entry.
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
                    pin_values[pin] = await self.async_get_pin(pin)
                else:
                    pin_values[pin] = edge == InterruptEdge.RISING

        return pin_values
