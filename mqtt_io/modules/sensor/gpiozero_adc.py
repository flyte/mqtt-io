"""
gpiozero analog to digital converter support
"""

import logging
from typing import TYPE_CHECKING

from mqtt_io.types import ConfigType, SensorValueType

from . import GenericSensor

if TYPE_CHECKING:
    # pylint: disable=import-error
    import gpiozero  # type: ignore

REQUIREMENTS = ("gpiozero",)

# This list comes from:
# https://gpiozero.readthedocs.io/en/stable/api_spi.html
ALLOWED_TYPES = ["MCP3001", "MCP3002", "MCP3004", "MCP3008",
                 "MCP3201", "MCP3202", "MCP3204", "MCP3208",
                 "MCP3301", "MCP3302", "MCP3304"]
CONFIG_SCHEMA = {
    "type": dict(
        type="string",
        required=True,
        empty=False,
        allowed=ALLOWED_TYPES + [x.upper() for x in ALLOWED_TYPES],
    ),
    "spi_port": dict(type="integer", required=False, empty=False, default=0),
    "spi_device": dict(type="integer", required=False, empty=False, default=0),
    "max_voltage": dict(type="float", required=False, empty=False, default=3.3),
    # NOTE:
    # Not all ADCs in the supported types list have 8 channels.
    # This is just the maximum allowed value.
    # The MCP3008/3208/3304 have 8 channels (0-7), while the MCP3004/3204/3302
    # have 4 channels (0-3), the MCP3002/3202 have 2 channels (0-1),
    # and the MCP3001/3201/3301 only have 1 channel.
    "channel": dict(
        type="integer",
        required=True,
        min=0,
        max=7,
    )
}

_LOG = logging.getLogger(__name__)


class Sensor(GenericSensor):
    """
    Implementation of gpiozero ADC sensor.
    """

    def setup_module(self) -> None:
        """
        Init the ADC on SPI
        """
        # pylint: disable=import-outside-toplevel,import-error
        import gpiozero

        cls = getattr(gpiozero, self.config["type"])
        self.adc = cls(channel=self.config["channel"],
                       max_voltage=self.config["max_voltage"],
                       port=self.config["spi_port"],
                       device=self.config["spi_device"])

    def get_value(self, sens_conf: ConfigType) -> SensorValueType:
        """
        Get the analog value from the adc for the configured channel
        """
        # Returns a float from 0 to max_voltage
        return self.adc.value
