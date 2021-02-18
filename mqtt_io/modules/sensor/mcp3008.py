"""
Sensor module for MCP3008.
"""

import logging
from typing import cast

from mqtt_io.types import ConfigType, SensorValueType

from . import GenericSensor

REQUIREMENTS = ("adafruit-mcp3008",)

CONFIG_SCHEMA = {
    "spi_port": dict(type="integer", required=False, empty=False, default=0),
    "chip_addr": dict(type="integer", required=False, empty=False, default=0),
}

_LOG = logging.getLogger("mqtt_gpio")


class Sensor(GenericSensor):
    """
    Implementation of MCP3008 ADC sensor.
    """

    SENSOR_SCHEMA = {
        "channel": dict(
            type="string",
            required=False,
            empty=False,
            default="CH0",
            allowed=[f"CH{i}" for i in range(8)] + [f"DF{i}" for i in range(8)],
        )
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
        self.channels = {f"CH{i}": i for i in range(8)}

    def get_value(self, sens_conf: ConfigType) -> SensorValueType:
        """
        Get the analog value from the adc for the configured channel
        """
        # Returns an integer from 0-1023
        return cast(int, self.mcp.read_adc(sens_conf["channel"]))
