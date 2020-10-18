from . import GenericSensor

REQUIREMENTS = ("adafruit-circuitpython-ahtx0",)


class Sensor(GenericSensor):
    """
    Implementation of Sensor class for aht20.
    """

    SENSOR_SCHEMA = {
        "type": dict(
            type="string",
            required=False,
            empty=False,
            default="temperature",
            allowed=["temperature", "humidity"],
        )
    }

    def __init__(self, config):
        import adafruit_ahtx0
        import board
        import busio

        i2c = busio.I2C(board.SCL, board.SDA)
        self.sensor = adafruit_ahtx0.AHTx0(i2c)

    def setup_sensor(self, config):
        return True  # nothing to do here

    def get_value(self, config):
        """get the temperature value from the sensor"""
        temperature = self.sensor.temperature
        humidity = self.sensor.relative_humidity
        if config["type"] == "temperature" and temperature is not None:
            return temperature
        if config["type"] == "humidity" and humidity is not None:
            return humidity
        return None
