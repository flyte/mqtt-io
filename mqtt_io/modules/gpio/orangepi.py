"""
Orange Pi GPIO
"""

from typing import Optional

from ...types import ConfigType, PinType
from . import GenericGPIO, PinDirection, PinPUD

ALLOWED_MODES = ["bcm", "board", "mode_soc"]
REQUIREMENTS = ("OPi.GPIO",)
CONFIG_SCHEMA = {
    "mode": {
        "type": "string",
        "required": True,
        "empty": False,
        "default": "bcm",
        "allowed": ALLOWED_MODES + list(map(str.upper, ALLOWED_MODES)),
    },
}


class GPIO(GenericGPIO):
    """
    Implementation of GPIO class for Orange Pi native GPIO.
    """

    def setup_module(self) -> None:
        # pylint: disable=import-outside-toplevel,import-error
        import OPi.GPIO as gpio  # type: ignore

        self.io = gpio
        self.direction_map = {
            PinDirection.INPUT: gpio.IN,
            PinDirection.OUTPUT: gpio.OUT,
        }
        self.pullup_map = {
            PinPUD.OFF: gpio.PUD_OFF,
            PinPUD.UP: gpio.PUD_UP,
            PinPUD.DOWN: gpio.PUD_DOWN,
        }

        mode = self.config["mode"].upper()
        gpio.setmode(getattr(gpio, mode))

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

        initial_int = {None: -1, "low": 0, "high": 1}[initial]
        try:
            self.io.setup(pin, direction, pull_up_down=pullup, initial=initial_int)
        except ValueError as exc:
            raise IOError(f"channel {pin} setup failed") from exc

    def set_pin(self, pin: PinType, value: bool) -> None:
        self.io.output(pin, value)

    def get_pin(self, pin: PinType) -> bool:
        return bool(self.io.input(pin))

    def cleanup(self) -> None:
        self.io.cleanup()
