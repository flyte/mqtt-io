"""
GPIO module for OrangePI on-board GPIO.
"""

from typing import Optional

from ...types import ConfigType, PinType
from . import GenericGPIO, PinDirection, PinPUD

ALLOWED_BOARDS = [
    "zero",
    "r1",
    "zeroplus",
    "zeroplus2h5",
    "zeroplus2h3",
    "pcpcplus",
    "one",
    "lite",
    "plus2e",
    "pc2",
    "prime",
]
ALLOWED_MODES = ["bcm", "board", "mode_soc"]
REQUIREMENTS = ("OrangePi.GPIO",)
CONFIG_SCHEMA = {
    "board": {
        "type": "string",
        "required": True,
        "empty": False,
        "allowed": ALLOWED_BOARDS + list(map(str.upper, ALLOWED_BOARDS)),
    },
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

        board = self.config["board"].upper()
        mode = self.config["mode"].upper()
        if not hasattr(gpio, board):
            raise AssertionError("%s board not found" % board)
        gpio.setboard(getattr(gpio, board))
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
