"""
GPIO module for Beaglebone.
"""
from typing import Any, Dict, Optional

from ...types import ConfigType, PinType
from . import GenericGPIO, PinDirection, PinPUD

REQUIREMENTS = ("Adafruit_BBIO",)

DIRECTIONS: Dict[PinDirection, Any] = {}
PULLUPS: Dict[PinPUD, Any] = {}


class GPIO(GenericGPIO):
    """
    Implementation of GPIO class for Beaglebone native GPIO.
    """

    def setup_module(self) -> None:
        # pylint: disable=global-statement,import-outside-toplevel,import-error
        global DIRECTIONS, PULLUPS
        import Adafruit_BBIO.GPIO as gpio  # type: ignore

        self.io = gpio
        DIRECTIONS = {PinDirection.INPUT: gpio.IN, PinDirection.OUTPUT: gpio.OUT}

        PULLUPS = {
            PinPUD.OFF: gpio.PUD_OFF,
            PinPUD.UP: gpio.PUD_UP,
            PinPUD.DOWN: gpio.PUD_DOWN,
        }

    def setup_pin(
        self,
        pin: PinType,
        direction: PinDirection,
        pullup: PinPUD,
        pin_config: ConfigType,
        initial: Optional[str] = None,
    ) -> None:
        direction = DIRECTIONS[direction]

        if pullup is None:
            pullup = PULLUPS[PinPUD.OFF]
        else:
            pullup = PULLUPS[pullup]

        initial_int = {None: -1, "low": 0, "high": 1}[initial]
        self.io.setup(pin, direction, pull_up_down=pullup, initial=initial_int)

    def set_pin(self, pin: PinType, value: bool) -> None:
        self.io.output(pin, value)

    def get_pin(self, pin: PinType) -> bool:
        return bool(self.io.input(pin))

    def cleanup(self) -> None:
        self.io.cleanup()
