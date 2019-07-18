"""BH1750 Light Intensity Sensor."""
from pi_mqtt_gpio.modules import GenericSensor


CONFIG_SCHEMA = {
    "i2c_bus_num": {"type": "integer", "required": True, "empty": False},
    "chip_addr": {"type": "integer", "required": True, "empty": False},
}

# Define some constants from the datasheet
DEVICE = 0x23       # Default device I2C address
POWER_DOWN = 0x00   # No active state
POWER_ON = 0x01     # Power on
RESET = 0x07        # Reset data register value
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
    """Implementation of Sensor class for the BH1750 light sensor."""

    def __init__(self, config):
        """Initialize sensor class."""
        import smbus

        self.bus = smbus.SMBus(config["i2c_bus_num"])
        self.address = config["chip_addr"]

    def setup_sensor(self, config):
        """Perform setup for the sensor."""
        return True  # nothing to do here

    def get_value(self, config):
        """Get the light value from the sensor."""
        value = self.bus.read_i2c_block_data(self.address,
                                             ONE_TIME_HIGH_RES_MODE_1)
        value = (value[1] + (256 * value[0])) / 1.2
        return value
