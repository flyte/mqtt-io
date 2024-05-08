"""
DS18S20/DS1822/DS18B20/DS1825/DS28EA00/MAX31850K temperature sensors
"""

from typing import Dict, cast

from ...types import ConfigType, SensorValueType
from . import GenericSensor

REQUIREMENTS = ("w1thermsensor>=2.0.0",)
ALLOWED_TYPES = ["DS18S20", "DS1822", "DS18B20", "DS1825", "DS28EA00", "MAX31850K"]
CONFIG_SCHEMA = {
    "address": {
        "type": 'string',
        "required": True,
        "empty": False
    },
    "type": {
        "type": 'string',
        "required": True,
        "empty": False,
        "allowed": ALLOWED_TYPES + [x.lower() for x in ALLOWED_TYPES],
    },
}


class Sensor(GenericSensor):
    """
    Implementation of Sensor class for the one wire temperature sensors. DS18B etc.
    """

    def setup_module(self) -> None:
        # pylint: disable=import-outside-toplevel,import-error
        from w1thermsensor import W1ThermSensor  # type: ignore
        from w1thermsensor.sensors import Sensor as SensorType  # type: ignore

        sensor_types: Dict[str, SensorType] = {s.name: s for s in list(SensorType)}
        self.sensor_type = sensor_types[self.config["type"].upper()]
        self.sensor = W1ThermSensor(self.sensor_type, self.config["address"].lower())

    def get_value(self, sens_conf: ConfigType) -> SensorValueType:
        """
        Get the temperature value from the sensor
        """
        return cast(float, self.sensor.get_temperature())
