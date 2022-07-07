"""
Raspberry Pi GPIO
"""

import logging
from typing import Any, Callable, Dict, List, Optional

from ...types import ConfigType, PinType
from . import GenericGPIO, InterruptEdge, InterruptSupport, PinDirection, PinPUD

_LOG = logging.getLogger(__name__)

REQUIREMENTS = ("RPi.GPIO",)


class GPIO(GenericGPIO):
    """
    Implementation of GPIO class for Raspberry Pi native GPIO.
    """

    INTERRUPT_SUPPORT = InterruptSupport.SOFTWARE_CALLBACK

    def setup_module(self) -> None:
        # pylint: disable=import-outside-toplevel,import-error
        import RPi.GPIO as gpio  # type: ignore

        self.io = gpio
        self.direction_map = {PinDirection.INPUT: gpio.IN, PinDirection.OUTPUT: gpio.OUT}

        self.pullup_map = {
            PinPUD.OFF: gpio.PUD_OFF,
            PinPUD.UP: gpio.PUD_UP,
            PinPUD.DOWN: gpio.PUD_DOWN,
        }

        self.interrupt_edge_map = {
            InterruptEdge.RISING: gpio.RISING,
            InterruptEdge.FALLING: gpio.FALLING,
            InterruptEdge.BOTH: gpio.BOTH,
        }

        gpio.setmode(gpio.BCM)

    def setup_pin(
        self,
        pin: PinType,
        direction: PinDirection,
        pullup: PinPUD,
        pin_config: ConfigType,
        initial: Optional[str] = None,
    ) -> None:
        direction = self.direction_map[direction]
        pullup = self.pullup_map[pullup]

        initial_int = {None: -1, "low": 0, "high": 1}[initial]
        self.io.setup(pin, direction, pull_up_down=pullup, initial=initial_int)

    def setup_interrupt_callback(
        self,
        pin: PinType,
        edge: InterruptEdge,
        in_conf: ConfigType,
        callback: Callable[[List[Any], Dict[Any, Any]], None],
    ) -> None:
        gpio_edge = self.interrupt_edge_map[edge]
        _LOG.debug(
            "Added interrupt to Raspberry Pi pin '%s' with callback '%s'", pin, callback
        )
        self.io.add_event_detect(
            pin,
            gpio_edge,
            callback=callback,
            bouncetime=in_conf.get("bouncetime", 100),
        )
        self.interrupt_edges[pin] = edge

    def get_interrupt_value(self, pin: PinType, *args: Any, **kwargs: Any) -> bool:
        edge = self.interrupt_edges[pin]
        if edge == InterruptEdge.BOTH:
            # Polling the pin for its value is a bit crap, but I can't find any alternative
            value = self.get_pin(pin)
        else:
            # If we're listening for RISING or FALLING then we infer the pin's value
            value = edge == InterruptEdge.RISING
        return value

    def set_pin(self, pin: PinType, value: bool) -> None:
        self.io.output(pin, value)

    def get_pin(self, pin: PinType) -> bool:
        return bool(self.io.input(pin))

    def cleanup(self) -> None:
        self.io.cleanup()
