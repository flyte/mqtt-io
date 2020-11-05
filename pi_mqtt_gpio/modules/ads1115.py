from pi_mqtt_gpio.modules import GenericSensor
import logging

REQUIREMENTS = ("adafruit-circuitpython-ads1x15",)

SENSOR_SCHEMA = {
    "channel": dict(
        type="string",
        required=False,
        empty=False,
        default="CH0",
        allowed=[
            "CH0",
            "CH1",
            "CH2",
            "CH3"
        ],
    )
}

_LOG = logging.getLogger("mqtt_gpio")


class Sensor(GenericSensor):
    """
    Implementation of ADS1115 ADC sensor.
    """

    def __init__(self, config):
        import time
        import board
        import busio
        import adafruit_ads1x15.ads1015 as ADS
        from adafruit_ads1x15.analog_in import AnalogIn

        # Create the I2C bus
        i2c = busio.I2C(board.SCL, board.SDA)

        # Create the ADC object using the I2C bus
        self.ads = ADS.ADS1115(i2c)

        self.channels = {
            "CH0": ADS.P0,
            "CH1": ADS.P1,
            "CH2": ADS.P2,
            "CH3": ADS.P3
        }

    def setup_sensor(self, config):
        return True  # nothing to do here

    def get_value(self, config):
        """get the analog value from the adc for the configured channel"""
        channel = self.channels.get(config["channel"], "invalid")
        _LOG.warning("MCP3008: Reading from channel %r", channel)
        if channel == "invalid":
            raise Exception("Channel '" + config["channel"] + "' not found!")
        chan = AnalogIn(self.ads, channel)
        _LOG.warning("MCP3008: value %d", chan.value)
        return chan.value

    def cleanup(self):
        """nothing to do here"""
        #self.adc.close()
