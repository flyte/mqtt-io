from pi_mqtt_gpio.modules import GenericSensor


REQUIREMENTS = ("spidev","mcp3008",)

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

class Sensor(GenericSensor):
    """
    Implementation of MCP3008 ADC sensor.
    """

    def __init__(self, config):
        import mcp3008

        """init the mcp on SPI CE0"""
        self.adc = mcp3008.MCP3008()
        
        self.channels = {
          "CH0": mcp3008.CH0,
          "CH1": mcp3008.CH1,
          "CH2": mcp3008.CH2,
          "CH3": mcp3008.CH3,
          "CH4": mcp3008.CH4,
          "CH5": mcp3008.CH5,
          "CH6": mcp3008.CH6,
          "CH7": mcp3008.CH7,
          "DF0": mcp3008.DF0,
          "DF1": mcp3008.DF1,
          "DF2": mcp3008.DF2,
          "DF3": mcp3008.DF3,
          "DF4": mcp3008.DF4,
          "DF5": mcp3008.DF5,
          "DF6": mcp3008.DF6,
          "DF7": mcp3008.DF7
    }

    def setup_sensor(self, config):
        return True  # nothing to do here

    def get_value(self, config):
        """get the analog value from the adc for the configured channel"""
        channel = self.channels.get(config.channel, "invalid")
        if channel == "invalid":
            raise Exception("Channel '" + config.channel + "' not found!")
        value = self.adc.read([channel])
        return value

    def cleanup(self):
        """close the adc, to proper shut down the spi bus"""
        self.adc.close()
