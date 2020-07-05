from pi_mqtt_gpio.modules import GenericSensor
import logging

REQUIREMENTS = ("spidev",)

SENSOR_SCHEMA = {
    "channel": dict(
        type="string",
        required=False,
        empty=False,
        default="CH0",
        allowed=["CH0", "CH1", "CH2", "CH3", "CH4", "CH5", "CH6", "CH7",
                 "DF0", "DF1", "DF2", "DF3", "DF4", "DF5", "DF6", "DF7"],
    )
}

_LOG = logging.getLogger("mqtt_gpio")

class Sensor(GenericSensor):
    """
    Implementation of MCP3008 ADC sensor.
    """

    def __init__(self, config):
        import spidev

        """init the mcp on SPI CE0"""
        self.spi = spidev.SpiDev()
        self.spi.open(0,0)

        self.channels = {
          "CH0": 0,
          "CH1": 1,
          "CH2": 2,
          "CH3": 3,
          "CH4": 4,
          "CH5": 5,
          "CH6": 6,
          "CH7": 7
        }

    def setup_sensor(self, config):
        return True  # nothing to do here

    def read_spi(self, channel):
        adc = self.spi.xfer2([1,(8+channel)<<4,0])
        _LOG.warning("MCP3008: adc %s", bytes(adc).hex())
        data = ((adc[1]&3) << 8) + adc[2]
        _LOG.warning("MCP3008: data %d", data)
        return data

    def get_value(self, config):
        """get the analog value from the adc for the configured channel"""
        channel = self.channels.get(config["channel"], "invalid")
        _LOG.warning("MCP3008: Reading from channel %r", channel)
        if channel == "invalid":
            raise Exception("Channel '" + config["channel"] + "' not found!")
        value = self.read_spi(channel)
        _LOG.warning("MCP3008: value %d", value)
        return value

    def cleanup(self):
        """close the adc, to proper shut down the spi bus"""
        #self.adc.close()
