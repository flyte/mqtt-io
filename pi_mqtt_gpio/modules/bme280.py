from pi_mqtt_gpio.modules import GenericSensor


REQUIREMENTS = ("smbus", "RPi.bme280")
CONFIG_SCHEMA = {
    "i2c_bus_num": dict(type="integer", required=True, empty=False),
    "chip_addr": dict(type="integer", required=True, empty=False),
}
SENSOR_SCHEMA = {
    "type": dict(
        type="string",
        required=False,
        empty=False,
        default="temperature",
        allowed=["temperature", "humidity", "pressure"],
    )
}


class Sensor(GenericSensor):
    """
    Implementation of Sensor class for the BME280 sensor.
    """

    def __init__(self, config):
        import smbus
        import bme280

        self.bus = smbus.SMBus(config["i2c_bus_num"])
        self.address = config["chip_addr"]
        self.calib = bme280.load_calibration_params(self.bus, self.address)

    def setup_sensor(self, config):
        return True  # nothing to do here

    def get_value(self, config):
        """get the temperature, humidity or pressure value from the sensor"""
        import bme280

        data = bme280.sample(self.bus, self.address, self.calib)

        if config["type"] == "temperature":
            return data.temperature
        if config["type"] == "humidity":
            return data.humidity
        if config["type"] == "pressure":
            return data.pressure
        return None
