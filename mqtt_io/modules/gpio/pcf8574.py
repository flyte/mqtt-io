"""
PCF8574 IO expander
"""

from typing import Optional, cast

from ...types import ConfigType, PinType
from . import GenericGPIO, PinDirection, PinPUD

REQUIREMENTS = ("pcf8574",)
CONFIG_SCHEMA = {
    "i2c_bus_num": {"type": "integer", "required": True, "empty": False},
    "chip_addr": {"type": "integer", "required": True, "empty": False},
}


class GPIO(GenericGPIO):
    """
    Implementation of GPIO class for the PCF8574 IO expander chip.
    """

    def setup_module(self) -> None:
        # pylint: disable=import-outside-toplevel,import-error
        # pylint: disable=no-name-in-module
        self.pullup_map = {PinPUD.OFF: None, PinPUD.UP: True, PinPUD.DOWN: False}
        from pcf8574 import PCF8574  # type: ignore

        self.io = PCF8574(self.config["i2c_bus_num"], self.config["chip_addr"])

    def setup_pin(
        self,
        pin: PinType,
        direction: PinDirection,
        pullup: PinPUD,
        pin_config: ConfigType,
        initial: Optional[str] = None,
    ) -> None:
        if direction == PinDirection.INPUT and self.pullup_map[pullup] is not None:
            self.io.port[pin] = self.pullup_map[pullup]
        initial = pin_config.get("initial")
        if initial is not None:
            if initial == "high":
                self.set_pin(pin, True)
            elif initial == "low":
                self.set_pin(pin, False)

    def set_pin(self, pin: PinType, value: bool) -> None:
        self.io.port[pin] = value

    def get_pin(self, pin: PinType) -> bool:
        return cast(bool, self.io.port[pin])
