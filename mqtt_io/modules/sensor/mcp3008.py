"""
MCP3008 analog to digital converter
"""

import logging
from typing import cast

from mqtt_io.types import ConfigType, SensorValueType

from . import GenericSensor

REQUIREMENTS = ("adafruit-mcp3008",)

CONFIG_SCHEMA = {
    "spi_port": {"type": 'integer', "required": False, "empty": False, "default": 0},
    "spi_device": {"type": 'integer', "required": False, "empty": False, "default": 0},
    "chip_addr": {"type": 'integer', "required": False, "empty": False, "default": 0},
}

_LOG = logging.getLogger(__name__)


class Sensor(GenericSensor):
    """
    Implementation of MCP3008 ADC sensor.
    """

    SENSOR_SCHEMA = {
        "channel": {"type": 'integer', "required": True, "min": 0, "max": 7}
    }

    def setup_module(self) -> None:
        """
        Init the mcp on SPI CE0
        """
        # pylint: disable=import-outside-toplevel,import-error
        import Adafruit_GPIO.SPI as SPI  # type: ignore
        import Adafruit_MCP3008  # type: ignore

        self.mcp = Adafruit_MCP3008.MCP3008(
            spi=SPI.SpiDev(self.config["spi_port"], self.config["spi_device"])
        )

    def get_value(self, sens_conf: ConfigType) -> SensorValueType:
        """
        Get the analog value from the adc for the configured channel
        """
        # Returns an integer from 0-1023
        return cast(int, self.mcp.read_adc(sens_conf["channel"]))
