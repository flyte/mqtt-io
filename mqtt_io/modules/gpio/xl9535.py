"""
XL9535/PCA9535/TCA9535 IO expander
"""

from typing import Optional, cast

from ...exceptions import RuntimeConfigError
from ...types import ConfigType, PinType
from . import GenericGPIO, PinDirection, PinPUD

REQUIREMENTS = ("smbus2",)
CONFIG_SCHEMA = {
    "i2c_bus_num": {"type": "integer", "required": True, "empty": False},
    "chip_addr": {"type": "integer", "required": True, "empty": False},
}

#XL9535_INPUT_PORT_0 = 0x00,
#XL9535_INPUT_PORT_1 = 0x01
XL9535_OUTPUT_PORT_0 = 0x02
#XL9535_OUTPUT_PORT_1 = 0x03
#XL9535_INVERSION_PORT_0 = 0x04
#XL9535_INVERSION_PORT_1 = 0x05
XL9535_CONFIG_PORT_0 = 0x06
#XL9535_CONFIG_PORT_1 = 0x07

class GPIO(GenericGPIO):
    """
    Implementation of GPIO class for the XL9535/PCA9535/TCA9535 IO expander chip.

    Pin numbers 0 - 15.
    """

    PIN_SCHEMA = {
        "pin": {"type": 'integer', "required": True, "min": 0, "max": 15},
    }

    def setup_module(self) -> None:
        # pylint: disable=import-outside-toplevel,import-error
        # pylint: disable=no-name-in-module
        from smbus2 import SMBus  # type: ignore

        self.bus = SMBus(self.config["i2c_bus_num"])
        self.address = self.config["chip_addr"]

        # configure all pins as outputs
        self.bus.write_word_data(self.address, XL9535_CONFIG_PORT_0, 0x0000)
        # off all outputs be default
        self.bus.write_word_data(self.address, XL9535_OUTPUT_PORT_0, 0x0000)

    def setup_pin(
        self,
        pin: PinType,
        direction: PinDirection,
        pullup: PinPUD,
        pin_config: ConfigType,
        initial: Optional[str] = None,
    ) -> None:
        # I han't found any ready-made expansion boards on sale where the chip works as an input.
        # For simplicity, the implementation only supports the chip working in output mode.
        if direction == PinDirection.INPUT:
            raise RuntimeConfigError("Unsupported PinDirection: INPUT")
        initial = pin_config.get("initial")
        if initial is not None:
            if initial == "high":
                self.set_pin(pin, True)
            elif initial == "low":
                self.set_pin(pin, False)

    def set_pin(self, pin: PinType, value: bool) -> None:
        assert pin in range(16), "Pin number must be an integer between 0 and 15"
        current_state = self.bus.read_word_data(self.address, XL9535_OUTPUT_PORT_0)
        bit = 1 << cast(int, pin)
        new_state = current_state | bit if value else current_state & (~bit & 0xffff)
        self.bus.write_word_data(self.address, XL9535_OUTPUT_PORT_0, new_state)

    def get_pin(self, pin: PinType) -> bool:
        assert pin in range(16), "Pin number must be an integer between 0 and 15"
        state = self.bus.read_word_data(self.address, XL9535_OUTPUT_PORT_0)
        return bool(state & 1 << cast(int, pin))

    def cleanup(self) -> None:
        self.bus.close()
