"""
PiFace Digital IO 2
"""

from typing import Optional

from ...types import ConfigType, PinType
from . import GenericGPIO, PinDirection, PinPUD

REQUIREMENTS = ("pifacedigitalio", "pifacecommon")


class GPIO(GenericGPIO):
    """
    Implementation of GPIO class for PiFaceDigital IO board.
    """

    def setup_module(self) -> None:
        # pylint: disable=import-outside-toplevel,import-error
        import pifacedigitalio as pfdio  # type: ignore

        pfdio.init()
        self.io = pfdio

    def setup_pin(
        self,
        pin: PinType,
        direction: PinDirection,
        pullup: PinPUD,
        pin_config: ConfigType,
        initial: Optional[str] = None,
    ) -> None:
        pass

    def set_pin(self, pin: PinType, value: bool) -> None:
        self.io.digital_write(pin, value)

    def get_pin(self, pin: PinType) -> bool:
        return bool(self.io.digital_read(pin))

    def cleanup(self) -> None:
        self.io.deinit()
