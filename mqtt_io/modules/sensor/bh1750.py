"""
BH1750 light level sensor
"""
from ...types import ConfigType, SensorValueType
from . import GenericSensor

REQUIREMENTS = ("smbus2",)

CONFIG_SCHEMA = {
    "i2c_bus_num": {"type": "integer", "required": True, "empty": False},
    "chip_addr": {"type": "integer", "required": True, "empty": False},
}

# Define some constants from the datasheet
DEVICE = 0x23  # Default device I2C address
POWER_DOWN = 0x00  # No active state
POWER_ON = 0x01  # Power on
RESET = 0x07  # Reset data register value
# Start measurement at 4lx resolution. Time typically 16ms.
CONTINUOUS_LOW_RES_MODE = 0x13
# Start measurement at 1lx resolution. Time typically 120ms
CONTINUOUS_HIGH_RES_MODE_1 = 0x10
# Start measurement at 0.5lx resolution. Time typically 120ms
CONTINUOUS_HIGH_RES_MODE_2 = 0x11
# Start measurement at 1lx resolution. Time typically 120ms
# Device is automatically set to Power Down after measurement.
ONE_TIME_HIGH_RES_MODE_1 = 0x20
# Start measurement at 0.5lx resolution. Time typically 120ms
# Device is automatically set to Power Down after measurement.
ONE_TIME_HIGH_RES_MODE_2 = 0x21
# Start measurement at 1lx resolution. Time typically 120ms
# Device is automatically set to Power Down after measurement.
ONE_TIME_LOW_RES_MODE = 0x23


class Sensor(GenericSensor):
    """
    Implementation of Sensor class for the BH1750 light sensor.
    """

    def setup_module(self) -> None:
        # pylint: disable=import-outside-toplevel,attribute-defined-outside-init,import-error
        from smbus2 import SMBus  # type: ignore

        self.SMBus = SMBus  # pylint: disable=invalid-name
        self.bus_num: int = self.config["i2c_bus_num"]
        self.address: int = self.config["chip_addr"]

    def get_value(self, sens_conf: ConfigType) -> SensorValueType:
        """
        Get the light value from the sensor.
        """
        with self.SMBus(self.bus_num) as bus:
            data = bus.read_i2c_block_data(self.address, ONE_TIME_HIGH_RES_MODE_1, 2)
            result = (data[1] + (256 * data[0])) / 1.2
            return float(result)
