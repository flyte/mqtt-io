"""
Sunxi Board
"""
from typing import Optional
from ...types import ConfigType, PinType
from . import GenericGPIO, PinDirection, PinPUD

REQUIREMENTS = ("pySUNXI",)

class GPIO(GenericGPIO):
    """
    Implementation of GPIO class for Sunxi native GPIO.
    """
    def setup_module(self) -> None:
        # pylint: disable=import-outside-toplevel,import-error
        from pySUNXI import gpio # type: ignore

        self.io: gpio = gpio
        self.direction_map = {PinDirection.INPUT: gpio.INPUT, PinDirection.OUTPUT: gpio.OUTPUT}

        self.pullup_map = {
            PinPUD.OFF: gpio.PULLNONE,
            PinPUD.UP: gpio.PULLUP,
            PinPUD.DOWN: gpio.PULLDOWN,
        }
        gpio.init()

    def setup_pin(
        self,
        pin: PinType,
        direction: PinDirection,
        pullup: PinPUD,
        pin_config: ConfigType,
        initial: Optional[str] = None,
    ) -> None:
        direction = self.direction_map[direction]

        if pullup is None:
            pullup = self.pullup_map[PinPUD.OFF]
        else:
            pullup = self.pullup_map[pullup]

        initial_state = {None: -1, "low": 0, "high": 1}[initial]
        #self.io.setup(pin, direction, pull_up_down=pullup, initial=initial)
        self.io.setcfg(pin, direction)
        self.io.pullup(pin, pullup)
        if direction==self.io.OUTPUT:
            self.io.output(pin, initial_state)

    def set_pin(self, pin: PinType, value: bool) -> None:
        self.io.output(pin, value)

    def get_pin(self, pin: PinType) -> bool:
        return bool(self.io.input(pin))

    def cleanup(self) -> None:
        pass
