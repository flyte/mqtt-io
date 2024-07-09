"""
AHT20 temperature and humidity sensor
"""

from typing import cast

from ...types import ConfigType, SensorValueType
from . import GenericSensor
from ...exceptions import RuntimeConfigError

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

    def setup_module(self) -> None:
        # pylint: disable=import-outside-toplevel,import-error
        import adafruit_ahtx0  # type: ignore
        import board  # type: ignore
        import busio  # type: ignore

        i2c = busio.I2C(board.SCL, board.SDA)
        self.sensor = adafruit_ahtx0.AHTx0(i2c)

    @property
    def _temperature(self) -> SensorValueType:
        return cast(SensorValueType, self.sensor.temperature)

    @property
    def _humidity(self) -> SensorValueType:
        return cast(SensorValueType, self.sensor.relative_humidity)

    def get_value(self, sens_conf: ConfigType) -> SensorValueType:
        """
        Get the temperature value from the sensor
        """
        if sens_conf["type"] == "temperature":
            return self._temperature
        if sens_conf["type"] == "humidity":
            return self._humidity
        raise RuntimeConfigError(
            "aht20 sensor '%s' was not configured to return 'temperature' or 'humidity'"
            % sens_conf["name"]
        )
