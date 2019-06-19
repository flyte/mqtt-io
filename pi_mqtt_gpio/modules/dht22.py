from pi_mqtt_gpio.modules import GenericSensor

REQUIREMENTS = ("Adafruit_DHT",)
ALLOWED_TYPES = ["dht11", "dht22", "am2302"]
CONFIG_SCHEMA = {
    "pin": dict(type="integer", required=True, empty=False),
    "type": dict(
        type="string", required=True, empty=False, allowed=ALLOWED_TYPES + list(map(str.upper, ALLOWED_TYPES))
    ),
}
SENSOR_SCHEMA = {
    "type": dict(
        type="string",
        required=False,
        empty=False,
        default="temperature",
        allowed=["temperature", "humidity"],
    )
}


class Sensor(GenericSensor):
    """
    Implementation of Sensor class for the DHT22 temperature sensor.
    """

    def __init__(self, config):
        import Adafruit_DHT as DHTsensor

        sensor_type = config["type"].lower()

        if sensor_type == "dht22":
            self.sensor_type = DHTsensor.DHT22
        elif sensor_type == "dht11":
            self.sensor_type = DHTsensor.DHT11
        elif sensor_type == "am2302":
            self.sensor_type = DHTsensor.AM2302
        else:
            raise Exception("Supported sensor types: DHT22, DHT11, AM2302")

        self.pin = config["pin"]
        self.sensor = DHTsensor

    def setup_sensor(self, config):
        return True  # nothing to do here

    def get_value(self, config):
        """get the temperature or humidity value from the sensor"""
        humidity, temperature = self.sensor.read_retry(self.sensor_type, self.pin)
        if config["type"] == "temperature" and temperature is not None:
            return temperature
        if config["type"] == "humidity" and humidity is not None:
            return humidity
        return None
