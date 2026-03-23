"""
DockerPi 4 Channel Relay GPIO
"""
from typing import Optional
from mqtt_io.modules.gpio import GenericGPIO, PinDirection, PinPUD
from ...types import ConfigType, PinType

REQUIREMENTS = ("smbus",)

CONFIG_SCHEMA = {
    "i2c_bus_num": {
        "type": "integer",
        "required": True,
        "empty": False,
        "default": 1,
    },
    "dev_addr": {
        "type": "integer",
        "required": True,
        "empty": False,
        "default": 0x11,
    },  # 0x10, 0x11, 0x12, 0x13
}

ON = 0x01
OFF = 0x00
DIRECTIONS = None
PULLUPS = None


class GPIO(GenericGPIO):
    """
    Implementation of DockerPi 4 chanel relay.
    """

    def setup_module(self) -> None:
        # pylint: disable=import-outside-toplevel,import-error
        import smbus as gpio  # type: ignore

        addr = self.config["dev_addr"]
        bus = self.config["i2c_bus_num"]
        self.bus = gpio.SMBus(bus)
        self.address = addr

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

    def set_pin(self, pin: PinType, value: bool) -> None:
        """Turn on/off relay number self.address"""
        self.bus.write_byte_data(self.address, pin, ON if value else OFF)

    def get_pin(self, pin: PinType) -> bool:
        return bool(self.bus.read_byte_data[self.address, pin])

    def cleanup(self) -> None:
        self.bus.close()
