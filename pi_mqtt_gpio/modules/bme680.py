from pi_mqtt_gpio.modules import GenericSensor


REQUIREMENTS = ("smbus", "bme680")
CONFIG_SCHEMA = {
    "i2c_bus_num": dict(type="integer", required=False, empty=False),
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
    Implementation of Sensor class for the BME680 sensor.
    """

    def __init__(self, config):
        import smbus
        import bme680

        self.i2c_addr = config["chip_addr"]
        self.i2c_device = smbus.SMBus(config["i2c_bus_num"])

    def setup_sensor(self, config):
        return True  # nothing to do here

    def get_value(self, config):
        """get the temperature, humidity or pressure value from the sensor"""
        import bme680

        data = bme680.BME680(self.i2c_addr, self.i2c_device)
        
        #Setup Oversample settings; these settings can be customized in the config file potentially
        data.set_humidity_oversample(bme680.OS_16X)
        data.set_pressure_oversample(bme680.OS_16X)
        data.set_temperature_oversample(bme680.OS_16X)
        data.set_filter(bme680.FILTER_SIZE_3)

        if config["type"] == "temperature":
            return data.data.temperature
        if config["type"] == "humidity":
            return data.data.humidity
        if config["type"] == "pressure":
            return data.data.pressure
        return None