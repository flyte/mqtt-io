"""
ADXL345 Digital Accelerometer Sensor

Mandatory:
- chip_addr

Optional:
- output_g (set True if output in g). default:m*s²

Output:
- x (in m*s²)
- y (in m*s²)
- z (in m*s²)
"""

from json import dumps
from typing import cast

from ...types import CerberusSchemaType, ConfigType, SensorValueType
from . import GenericSensor

REQUIREMENTS = ("adxl345",)
CONFIG_SCHEMA: CerberusSchemaType = {
    "chip_addr": {"type": 'integer', "required": True, "empty": False},
    "output_g": {"type": 'boolean', "required": False, "empty": False},
}


class Sensor(GenericSensor):
    """
    Implementation of Sensor class for the ADXL345 sensor.
    """

    SENSOR_SCHEMA: CerberusSchemaType = {
        "type": {
            "type": 'string',
            "required": False,
            "empty": False,
            "default": 'all',
            "allowed": ['all', 'x', 'y', 'z'],
        }
    }

    def setup_module(self) -> None:
        # pylint: disable=import-outside-toplevel,attribute-defined-outside-init
        # pylint: disable=import-error,no-member
        from adxl345 import ADXL345  # type: ignore

        self.i2c_addr: int = self.config["chip_addr"]
        self.adxl345 = ADXL345(self.i2c_addr)

    def get_value(self, sens_conf: ConfigType) -> SensorValueType:
        sens_type = sens_conf["type"]

        if "output_g" in self.config and self.config["output_g"]:
            all_axes = self.adxl345.get_axes(True)
        else:
            all_axes = self.adxl345.get_axes()

        return cast(
            float,
            {
                "x": all_axes['x'],
                "y": all_axes['y'],
                "z": all_axes['z'],
                "all_axes": dumps(all_axes),
            }[sens_type],
        )
