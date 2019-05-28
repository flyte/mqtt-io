from pi_mqtt_gpio.modules import GenericSensor


REQUIREMENTS = ("Adafruit_DHT",)
CONFIG_SCHEMA = {
    "pin": {"type": "integer", "required": True, "empty": False},
    "sensor_type": {"type": "string", "required": True, "empty": False}
}


class Sensor(GenericSensor):
    """
    Implementation of Sensor class for the DHT22 temperature sensor.
    """

    def __init__(self, config):
        import Adafruit_DHT as DHTsensor
        sensor_type = config["sensor_type"].lower()

        if sensor_type == 'dht22':
            self.sensor_type = DHTsensor.DHT22
        elif sensor_type == 'dht11':
            self.sensor_type = DHTsensor.dht11
        elif sensor_type == 'am2302':
            self.sensor_type = DHTsensor.AM2302
        else:
            raise Exception('Supported sensor types: DHT22, DHT11, AM2302')        
        
        self.pin = config["pin"]
        self.sensor = DHTsensor        

    def setup_sensor(self, config):
        return True  # nothing to do here

    def get_value(self, sensor, options):
        """get the temperature or humidity value from the sensor"""
        humidity, temperature = self.sensor.read_retry(self.sensor_type, self.pin)
        if humidity is not None and temperature is not None:
          if options["type"] == "temperature" :
            return temperature
          if options["type"] == "humidity" :
            return humidity
        return float('NAN')

