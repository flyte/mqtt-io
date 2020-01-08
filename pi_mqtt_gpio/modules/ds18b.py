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

        sensor_config_type = config["type"]
        
        #get the sensor type mapping
        self.sensor_type = None
        for w1_sensor_type, w1_sensor_name in TYPE_NAMES.items():    # for name, age in dictionary.iteritems():  (for Python 2.x)
            if w1_sensor_name.lower() == sensor_config_type.lower():
                self.sensor_type = w1_sensor_type
        
        # initialization failed
        if self.sensor_type is None:
            print("Supported sensor types: " + str(TYPE_NAMES.values()))
     
        self.sensor = W1ThermSensor(self.sensor_type, config["address"].lower())

    def setup_sensor(self, config):
        return True  # nothing to do here

    def get_value(self, config):
        """get the temperature value from the sensor"""
        temperature = self.sensor.get_temperature()
        return temperature
