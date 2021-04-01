"""
GPIO module for writing outputs to the console. Used for testing.
"""

from typing import Optional

from ...types import ConfigType, PinType
from . import GenericGPIO, PinDirection, PinPUD


class GPIO(GenericGPIO):
    """
    Implementation of GPIO class for outputting to STDIO.
    """

    def setup_module(self) -> None:
        print("setup_module()")

    def setup_pin(
        self,
        pin: PinType,
        direction: PinDirection,
        pullup: PinPUD,
        pin_config: ConfigType,
        initial: Optional[str] = None,
    ) -> None:
        print(
            "setup_pin(pin=%r, direction=%r, pullup=%r, pin_config=%r, initial=%r)"
            % (pin, direction, pullup, pin_config, initial)
        )
        if initial == "high":
            self.set_pin(pin, True)
        elif initial == "low":
            self.set_pin(pin, False)

    async def async_set_pin(self, pin: PinType, value: bool) -> None:
        self.set_pin(pin, value)

    def set_pin(self, pin: PinType, value: bool) -> None:
        print("set_pin(pin=%r, value=%r)" % (pin, value))

    async def async_get_pin(self, pin: PinType) -> bool:
        return self.get_pin(pin)

    def get_pin(self, pin: PinType) -> bool:
        print("get_pin(pin=%r)" % pin)
        return False
