from pi_mqtt_gpio.modules import GenericSensor


REQUIREMENTS = ("smbus",)

CONFIG_SCHEMA = {
    "i2c_bus_num": {"type": "integer", "required": True, "empty": False},
    "chip_addr": {"type": "integer", "required": True, "empty": False},
}

LM75_TEMP_REGISTER = 0


class Sensor(GenericSensor):
    """
    Implementation of Sensor class for the LM75 temperature sensor.
    """

    def __init__(self, config):
        import smbus

        self.bus = smbus.SMBus(config["i2c_bus_num"])
        self.address = config["chip_addr"]

    def setup_sensor(self, config):
        return True  # nothing to do here

    def get_value(self, config):
        """get the temperature value from the sensor"""
        value = self.bus.read_word_data(self.address, LM75_TEMP_REGISTER) & 0xFFFF
        value = ((value << 8) & 0xFF00) + (value >> 8)
        return self.convert_to_celsius(value)

    def convert_to_celsius(self, value):
        return (value / 32.0) / 8.0
