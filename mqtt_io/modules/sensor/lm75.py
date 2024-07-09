"""
LM75 temperature sensor
"""

from mqtt_io.types import ConfigType, SensorValueType
from . import GenericSensor

REQUIREMENTS = ("smbus2",)

CONFIG_SCHEMA = {
    "i2c_bus_num": {"type": "integer", "required": True, "empty": False},
    "chip_addr": {"type": "integer", "required": True, "empty": False},
}

LM75_TEMP_REGISTER = 0


class Sensor(GenericSensor):
    """
    Implementation of Sensor class for the LM75 temperature sensor.
    """

    def setup_module(self) -> None:
        # pylint: disable=import-outside-toplevel,import-error
        from smbus2 import SMBus  # type: ignore

        self.bus = SMBus(self.config["i2c_bus_num"])
        self.address = self.config["chip_addr"]

    def get_value(self, sens_conf: ConfigType) -> SensorValueType:
        """
        Get the temperature value from the sensor
        """
        value: int = self.bus.read_word_data(self.address, LM75_TEMP_REGISTER) & 0xFFFF
        value = ((value << 8) & 0xFF00) + (value >> 8)
        celsius: float = (value / 32.0) / 8.0
        return celsius
