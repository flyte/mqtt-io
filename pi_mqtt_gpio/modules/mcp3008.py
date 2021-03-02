from pi_mqtt_gpio.modules import GenericSensor
import logging

REQUIREMENTS = ("gpiozero",)

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
            "CH3",
            "CH4",
            "CH5",
            "CH6",
            "CH7",
            "DF0",
            "DF1",
            "DF2",
            "DF3",
            "DF4",
            "DF5",
            "DF6",
            "DF7",
        ],
    )
}

_LOG = logging.getLogger("mqtt_gpio")


class Sensor(GenericSensor):
    """
    Implementation of MCP3008 ADC sensor.
    """

    def __init__(self, config):
        from gpiozero import MCP3008

        """init the mcp on SPI CE0"""
        SPI_PORT = 0
        SPI_DEVICE = 0
        SPI_CHANNEL = 0

        self.channels = {
            "CH0": 0,
            "CH1": 1,
            "CH2": 2,
            "CH3": 3,
            "CH4": 4,
            "CH5": 5,
            "CH6": 6,
            "CH7": 7,
        }

        self.mcp = MCP3008(channel=SPI_CHANNEL, port=SPI_PORT, device=SPI_DEVICE)

    def setup_sensor(self, config):
        return True  # nothing to do here

    def get_value(self, config):
        """get the analog value from the adc for the configured channel"""
        channel = self.channels.get(config["channel"], "invalid")
        if channel == "invalid":
            raise Exception("Channel '" + config["channel"] + "' not found!")
        self.mcp._channel = channel
        _LOG.warning("MCP3008: Reading from channel %r", self.mcp.channel)
        value = self.mcp.value
        _LOG.warning("MCP3008: value %d", value)
        return value

    def cleanup(self):
        """close the adc, to proper shut down the spi bus"""
        # self.adc.close()
