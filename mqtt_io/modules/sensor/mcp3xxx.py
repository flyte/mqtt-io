"""
MCP3xxx analog to digital converter via GPIOZero
"""

from ...exceptions import RuntimeConfigError
from ...types import ConfigType, SensorValueType
from . import GenericSensor

REQUIREMENTS = ("gpiozero",)
ALLOWED_TYPES = [
    "MCP3001",
    "MCP3002",
    "MCP3004",
    "MCP3008",
    "MCP3201",
    "MCP3202",
    "MCP3204",
    "MCP3208",
    "MCP3301",
    "MCP3302",
    "MCP3304",
    "MCP3308",
]
CONFIG_SCHEMA = {
    "spi_port": {"type": 'integer', "required": False, "empty": False, "default": 0},
    "spi_device": {"type": 'integer', "required": False, "empty": False, "default": 0},
    "type": {
        "type": 'string',
        "required": True,
        "empty": False,
        "allowed": ALLOWED_TYPES + [x.lower() for x in ALLOWED_TYPES],
    },
    "channel": {"type": 'integer', "required": False, "empty": False, "default": 0},
    "differential": {"type": 'boolean', "required": False, "empty": False, "default": False},
    "max_voltage": {"type": 'float', "required": False, "empty": False, "default": 3.3},
}


class Sensor(GenericSensor):
    """
    Implementation of MCP3xxx ADC sensor via gpiozero.
    """

    # pylint: disable=too-many-locals,too-many-branches
    def setup_module(self) -> None:
        """
        Init the mcp on SPI CEx
        """

        # read config values
        sensor_spi_port: int = self.config["spi_port"]
        sensor_spi_device: int = self.config["spi_device"]
        sensor_type: str = self.config["type"].upper()
        sensor_channel: int = self.config["channel"]
        sensor_differential: bool = self.config["differential"]
        sensor_max_voltage: float = self.config["max_voltage"]

        # import sensor supertype
        # pylint: disable=import-outside-toplevel,import-error
        from gpiozero import AnalogInputDevice  # type: ignore

        # init the sensor by type
        self.mcp: AnalogInputDevice

        if sensor_type == "MCP3001":
            # pylint: disable=import-outside-toplevel,import-error
            from gpiozero import MCP3001

            self.mcp = MCP3001(
                max_voltage=sensor_max_voltage,
                port=sensor_spi_port,
                device=sensor_spi_device,
            )
        elif sensor_type == "MCP3002":
            # pylint: disable=import-outside-toplevel,import-error
            from gpiozero import MCP3002

            self.mcp = MCP3002(
                channel=sensor_channel,
                differential=sensor_differential,
                max_voltage=sensor_max_voltage,
                port=sensor_spi_port,
                device=sensor_spi_device,
            )
        elif sensor_type == "MCP3004":
            # pylint: disable=import-outside-toplevel,import-error
            from gpiozero import MCP3004

            self.mcp = MCP3004(
                channel=sensor_channel,
                differential=sensor_differential,
                max_voltage=sensor_max_voltage,
                port=sensor_spi_port,
                device=sensor_spi_device,
            )
        elif sensor_type == "MCP3008":
            # pylint: disable=import-outside-toplevel,import-error
            from gpiozero import MCP3008

            self.mcp = MCP3008(
                channel=sensor_channel,
                differential=sensor_differential,
                max_voltage=sensor_max_voltage,
                port=sensor_spi_port,
                device=sensor_spi_device,
            )
        elif sensor_type == "MCP3201":
            # pylint: disable=import-outside-toplevel,import-error
            from gpiozero import MCP3201

            self.mcp = MCP3201(
                max_voltage=sensor_max_voltage,
                port=sensor_spi_port,
                device=sensor_spi_device,
            )
        elif sensor_type == "MCP3202":
            # pylint: disable=import-outside-toplevel,import-error
            from gpiozero import MCP3202

            self.mcp = MCP3202(
                channel=sensor_channel,
                differential=sensor_differential,
                max_voltage=sensor_max_voltage,
                port=sensor_spi_port,
                device=sensor_spi_device,
            )
        elif sensor_type == "MCP3204":
            # pylint: disable=import-outside-toplevel,import-error
            from gpiozero import MCP3204

            self.mcp = MCP3204(
                channel=sensor_channel,
                differential=sensor_differential,
                max_voltage=sensor_max_voltage,
                port=sensor_spi_port,
                device=sensor_spi_device,
            )
        elif sensor_type == "MCP3208":
            # pylint: disable=import-outside-toplevel,import-error
            from gpiozero import MCP3208

            self.mcp = MCP3208(
                channel=sensor_channel,
                differential=sensor_differential,
                max_voltage=sensor_max_voltage,
                port=sensor_spi_port,
                device=sensor_spi_device,
            )
        elif sensor_type == "MCP3301":
            # pylint: disable=import-outside-toplevel,import-error
            from gpiozero import MCP3301

            self.mcp = MCP3301(
                max_voltage=sensor_max_voltage,
                port=sensor_spi_port,
                device=sensor_spi_device,
            )
        elif sensor_type == "MCP3302":
            # pylint: disable=import-outside-toplevel,import-error
            from gpiozero import MCP3302

            self.mcp = MCP3302(
                channel=sensor_channel,
                differential=sensor_differential,
                max_voltage=sensor_max_voltage,
                port=sensor_spi_port,
                device=sensor_spi_device,
            )
        elif sensor_type == "MCP3304":
            # pylint: disable=import-outside-toplevel,import-error
            from gpiozero import MCP3304

            self.mcp = MCP3304(
                channel=sensor_channel,
                differential=sensor_differential,
                max_voltage=sensor_max_voltage,
                port=sensor_spi_port,
                device=sensor_spi_device,
            )
        elif sensor_type == "MCP3308":
            # pylint: disable=import-outside-toplevel,import-error
            from gpiozero import MCP3308

            self.mcp = MCP3308(
                channel=sensor_channel,
                differential=sensor_differential,
                max_voltage=sensor_max_voltage,
                port=sensor_spi_port,
                device=sensor_spi_device,
            )
        else:
            raise RuntimeConfigError("Unsupported MCP type: %s" % sensor_type)

    def get_value(self, sens_conf: ConfigType) -> SensorValueType:
        """
        Get the analog value from the adc for the configured channel
        """
        # Returns an float between 0 and 1 (or -1 to +1 for certain devices operating in
        # differential mode)
        return float(self.mcp.value)
