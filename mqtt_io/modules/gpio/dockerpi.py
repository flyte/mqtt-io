"""
DockerPi 4 Channel Relay GPIO
"""
from ...types import ConfigType, PinType
from mqtt_io.modules.gpio import GenericGPIO, PinDirection, PinPUD

REQUIREMENTS = ("smbus",)

CONFIG_SCHEMA = {
    "i2c_bus_num": {"type": "integer", "required": True, "empty": False}, # 1
    "dev_addr": {"type": "integer", "required": True, "empty": False}, # 0x10, 0x11, 0x12, 0x13
}

ON = 0xFF
OFF = 0x00
DIRECTIONS = None
PULLUPS = None

class GPIO(GenericGPIO):
    """
    Implementation of DockerPi 4 chanel relay.
    """
    def setup_module(self) -> None:
        import smbus
        self.bus = smbus.SMBus(config["i2c_bus_num"])
        self.address = config["dev_addr"]

    def setup_pin(
        self,
        pin: PinType,
        direction: PinDirection,
        pullup: PinPUD,
        pin_config: ConfigType,
    ) -> None:

    def set_pin(self, pin: PinType, value: bool) -> None:
        """ Turn on/off relay number self.address """
        self.bus.write_byte_data(self.address, pin, value)

    def get_pin(self, pin: PinType) -> bool:
        return bool(self.bus.read_byte_data[self.address, pin])

    def cleanup(self) -> None:
        self.bus.close()
