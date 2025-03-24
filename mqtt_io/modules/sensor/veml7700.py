"""
VEML7700 luminosity sensor
"""
from typing import cast

from ...types import CerberusSchemaType, ConfigType, SensorValueType
from . import GenericSensor

REQUIREMENTS = ("adafruit-circuitpython-veml7700",)
CONFIG_SCHEMA: CerberusSchemaType = {
    "chip_addr": {
        "type": 'integer',
        "required": False,
        "empty": False,
        "default": '0x10'},
    "integration_time": {
        "required": False,
        "empty": False,
        "allowed": [25, 50, 100, 200, 400, 800],
        "default": 25,
    },
    "gain": {
        "required": False,
        "empty": False,
        "allowed": [0.125, 0.25, 1, 2],
        "default": 0.125,
    },
}


class Sensor(GenericSensor):
    """
    Implementation of Sensor class for the Adafruit_VEML7700
    """

    SENSOR_SCHEMA: CerberusSchemaType = {
        "type": {
            "type": 'string',
            "required": False,
            "empty": False,
            "allowed": ['light', 'lux', 'lux_corrected'],
            "default": 'lux_corrected',
        },
    }

    def setup_module(self) -> None:
        # pylint: disable=import-outside-toplevel,attribute-defined-outside-init
        # pylint: disable=import-error,no-member
        import board  # type: ignore
        import busio  # type: ignore
        import adafruit_veml7700 # type: ignore
        # Create the I2C bus
        self.i2c = busio.I2C(board.SCL, board.SDA)

        # Convert sensor address from hex to dec
        self.address = int(0x10)
        if self.config["chip_addr"]:
            self.address = int(self.config["chip_addr"])

        self.veml7700 = adafruit_veml7700.VEML7700(self.i2c, self.address)

        # Set gain
        gains = {
            "0.125": 'ALS_GAIN_1_8',
            "0.25": 'ALS_GAIN_1_4',
            "1": 'ALS_GAIN_1',
            "2": 'ALS_GAIN_2',
        }
        if 'gain' in self.config:
            self.veml7700.light_gain = getattr(self.veml7700, gains[str(self.config['gain'])])

        # Set integration time
        ints = {
            "25": 'ALS_25MS',
            "50": 'ALS_50MS',
            "100": 'ALS_100MS',
            "200": 'ALS_200MS',
            "400": 'ALS_400MS',
            "800": 'ALS_800MS',
        }
        if 'integration_time' in self.config:
            self.veml7700.light_integration_time = getattr(self.veml7700,
                ints[str(self.config['integration_time'])])

        #print("veml7700 Gain = {}".format(self.veml7700.light_gain))
        #print("veml7700 Integration time = {}".format(self.veml7700.light_integration_time))

    def get_value(self, sens_conf: ConfigType) -> SensorValueType:
        # pylint: disable=import-outside-toplevel,attribute-defined-outside-init
        # pylint: disable=import-error,no-member
        sens_type = sens_conf["type"]
        data = {
            "light": self.veml7700.light,
            "lux": self.veml7700.lux,
            "lux_corrected": "-1",
        }

        if data['lux'] > 1000:
            data['lux_corrected'] = (6.0135e-13 * data['lux'] ** 4) + \
                (-9.3924e-9 * data['lux'] ** 3) + \
                (8.1488e-5 * data['lux'] ** 2) + \
                (1.0023 * data['lux'])
        else:
            data['lux_corrected'] = data['lux']

        return cast(
            float,
            data[sens_type],
        )
