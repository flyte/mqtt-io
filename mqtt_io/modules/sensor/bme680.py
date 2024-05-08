"""
BME680 temperature, humidity and pressure sensor
"""

from typing import cast

from ...types import CerberusSchemaType, ConfigType, SensorValueType
from . import GenericSensor

REQUIREMENTS = ("smbus2", "bme680")
CONFIG_SCHEMA = {
    "i2c_bus_num": {"type": 'integer', "required": False, "empty": False},
    "chip_addr": {"type": 'integer', "required": True, "empty": False},
}


class Sensor(GenericSensor):
    """
    Implementation of Sensor class for the BME680 sensor.
    """

    SENSOR_SCHEMA: CerberusSchemaType = {
        "type": {
            "type": 'string',
            "required": False,
            "default": 'temperature',
            "allowed": ['temperature', 'humidity', 'pressure'],
        },
        "oversampling": {
            "type": 'string',
            "required": False,
            "allowed": ['none', '1x', '2x', '4x', '8x', '16x'],
        },
    }

    def setup_module(self) -> None:
        # pylint: disable=import-outside-toplevel,attribute-defined-outside-init
        # pylint: disable=import-error,no-member
        from smbus2 import SMBus  # type: ignore
        import bme680  # type: ignore

        # self.address: int = self.config["chip_addr"]
        self.i2c_addr: int = self.config["chip_addr"]
        self.i2c_device = SMBus(self.config["i2c_bus_num"])
        self.sensor = bme680.BME680(self.i2c_addr, self.i2c_device)

        self.oversampling_map = {
            "none": bme680.OS_NONE,
            "1x": bme680.OS_1X,
            "2x": bme680.OS_2X,
            "4x": bme680.OS_4X,
            "8x": bme680.OS_8X,
            "16x": bme680.OS_16X,
        }

    def setup_sensor(self, sens_conf: ConfigType) -> None:
        sens_type: str = sens_conf["type"]
        if "oversampling" in sens_conf:
            set_oversampling = getattr(self.sensor, f"set_{sens_type}_oversample")
            set_oversampling(self.oversampling_map[sens_conf["oversampling"]])

    def get_value(self, sens_conf: ConfigType) -> SensorValueType:
        sens_type = sens_conf["type"]
        if not self.sensor.get_sensor_data():
            return None
        return cast(
            float,
            {
                "temperature": self.sensor.data.temperature,
                "humidity": self.sensor.data.humidity,
                "pressure": self.sensor.data.pressure,
            }[sens_type],
        )
