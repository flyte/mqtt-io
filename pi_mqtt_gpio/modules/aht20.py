from pi_mqtt_gpio.modules import GenericSensor


REQUIREMENTS = ("adafruit-circuitpython-ahtx0",)

class Sensor(GenericSensor):
    """
    Implementation of GPIO class for Beaglebone native GPIO.
    """

    def __init__(self, config):
        import board
        import busio
        import adafruit_ahtx0

        self.i2c = busio.I2C(board.SCL, board.SDA)
        self.sensor = adafruit_ahtx0.AHTx0(i2c)

    def setup_sensor(self, config):
        return True  # nothing to do here

    def get_value(self, config):
        """get the temperature value from the sensor"""
        temperature = self.sensor.temperature
        humidity = self.sensor.humidity
        if config["type"] == "temperature" and temperature is not None:
            return temperature
        if config["type"] == "humidity" and humidity is not None:
            return humidity
        return None

