"""
BMP085 temperature and pressure sensor
"""

from typing import cast

from ...types import CerberusSchemaType, ConfigType, SensorValueType
from . import GenericSensor

REQUIREMENTS = ("Adafruit_BMP",)
CONFIG_SCHEMA: CerberusSchemaType = {
    "chip_addr": {"type": 'integer', "required": True, "empty": False},
}
DATA_READER = {
        "temperature": lambda bmp: bmp.read_temperature(),
        "pressure": lambda bmp: bmp.read_pressure(),
        "altitude": lambda bmp: bmp.read_altitude(),
}


class Sensor(GenericSensor):
    """
    Implementation of Sensor class for the BME280 sensor.
    """

    SENSOR_SCHEMA: CerberusSchemaType = {
        "type": {
            "type": 'string',
            "required": False,
            "empty": False,
            "default": 'temperature',
            "allowed": ['temperature', 'pressure', 'altitude'],
        }
    }

    def setup_module(self) -> None:
        # pylint: disable=import-outside-toplevel,attribute-defined-outside-init
        # pylint: disable=import-error,no-member
        from Adafruit_BMP.BMP085 import BMP085 # type: ignore

        self.address: int = self.config["chip_addr"]
        self.bmp = BMP085(address=self.address)

    def get_value(self, sens_conf: ConfigType) -> SensorValueType:
        """
        Get the temperature, humidity or pressure value from the sensor
        """
        sens_type = sens_conf["type"]
        #error: Call to untyped function (unknown) in typed context
        data = DATA_READER[sens_type](self.bmp) # type: ignore
        return cast(float, data)
