"""
GPIO module for PCF8574.
"""

from typing import Any, Dict, Optional, cast

from ...types import ConfigType, PinType
from . import GenericGPIO, PinDirection, PinPUD

REQUIREMENTS = ("pcf8574",)
CONFIG_SCHEMA = {
    "i2c_bus_num": {"type": "integer", "required": True, "empty": False},
    "chip_addr": {"type": "integer", "required": True, "empty": False},
}

PULLUPS: Dict[PinPUD, Any] = {}


class GPIO(GenericGPIO):
    """
    Implementation of GPIO class for the PCF8574 IO expander chip.
    """

    def setup_module(self) -> None:
        # pylint: disable=global-statement,import-outside-toplevel,import-error
        global PULLUPS
        PULLUPS = {PinPUD.UP: True, PinPUD.DOWN: False}
        from pcf8574 import PCF8574

        self.io = PCF8574(self.config["i2c_bus_num"], self.config["chip_addr"])

    def setup_pin(
        self,
        pin: PinType,
        direction: PinDirection,
        pullup: PinPUD,
        pin_config: ConfigType,
        initial: Optional[str] = None,
    ) -> None:
        if direction == PinDirection.INPUT and pullup is not None:
            self.io.port[pin] = PULLUPS[pullup]
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
