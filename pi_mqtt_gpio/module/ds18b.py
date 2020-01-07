from pi_mqtt_gpio.modules import GenericSensor

REQUIREMENTS = ("w1thermsensor",)
ALLOWED_TYPES = ["DS18S20", "DS1822", "DS18B20", "DS1825", "DS28EA00", "MAX31850K"] //take from w1thermsensor (?)
CONFIG_SCHEMA = {
    "address": dict(type="string", required=True, empty=False),
    "type": dict(
        type="string", required=True, empty=False, allowed=ALLOWED_TYPES + list(map(str.lower, ALLOWED_TYPES))
    ),
}

class Sensor(GenericSensor):
    """
    Implementation of Sensor class for the DHT22 temperature sensor.
    """

    def __init__(self, config):
        from w1thermsensor import W1ThermSensor

        sensor_type = config["type"].lower()
"""
   TYPE_NAMES = {
        THERM_SENSOR_DS18S20: "DS18S20",
        THERM_SENSOR_DS1822: "DS1822",
        THERM_SENSOR_DS18B20: "DS18B20",
        THERM_SENSOR_DS1825: "DS1825",
        THERM_SENSOR_DS28EA00: "DS28EA00",
        THERM_SENSOR_MAX31850K: "MAX31850K",
    }
"""
        if sensor_type == "DS18S20":
            self.sensor_type = W1ThermSensor.THERM_SENSOR_DS18S20
        elif sensor_type == "DS1822":
            self.sensor_type = W1ThermSensor.THERM_SENSOR_DS1822
        elif sensor_type == "DS18B20":
            self.sensor_type = W1ThermSensor.THERM_SENSOR_DS18B20
        elif sensor_type == "DS28EA00":
            self.sensor_type = W1ThermSensor.THERM_SENSOR_DS1825
        elif sensor_type == "DS1825/MAX31850K":
            self.sensor_type = W1ThermSensor.THERM_SENSOR_MAX31850K
        else:
            raise Exception("Supported sensor types: xxx) //take from W1ThermSensor array?

        self.sensor = W1ThermSensor(self.sensor_type, config["address"].lower())

    def setup_sensor(self, config):
        return True  # nothing to do here

    def get_value(self, config):
        """get the temperature value from the sensor"""
        temperature = self.sensor.get_temperature()
        return temperature
