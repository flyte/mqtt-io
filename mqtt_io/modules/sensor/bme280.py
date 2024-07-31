"""
BME280 temperature, humidity and pressure sensor
"""

from typing import cast

from ...types import CerberusSchemaType, ConfigType, SensorValueType
from . import GenericSensor

REQUIREMENTS = ("smbus2", "RPi.bme280")
CONFIG_SCHEMA: CerberusSchemaType = {
    "i2c_bus_num": {"type": 'integer', "required": True, "empty": False},
    "chip_addr": {"type": 'integer', "required": True, "empty": False},
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
            "allowed": ['temperature', 'humidity', 'pressure'],
        }
    }

    def setup_module(self) -> None:
        # pylint: disable=import-outside-toplevel,attribute-defined-outside-init
        # pylint: disable=import-error,no-member
        from smbus2 import SMBus  # type: ignore
        import bme280  # type: ignore

        self.bus = SMBus(self.config["i2c_bus_num"])
        self.address: int = self.config["chip_addr"]
        self.bme = bme280
        self.calib = bme280.load_calibration_params(self.bus, self.address)

    def get_value(self, sens_conf: ConfigType) -> SensorValueType:
        """
        Get the temperature, humidity or pressure value from the sensor
        """
        sens_type = sens_conf["type"]
        data = self.bme.sample(self.bus, self.address, self.calib)
        return cast(
            float,
            {
                "temperature": data.temperature,
                "humidity": data.humidity,
                "pressure": data.pressure,
            }[sens_type],
        )
