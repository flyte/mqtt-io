"""
TSL2561 luminosity sensor
"""
from typing import cast

from ...types import CerberusSchemaType, ConfigType, SensorValueType
from . import GenericSensor

REQUIREMENTS = ("adafruit-circuitpython-tsl2561",)
CONFIG_SCHEMA: CerberusSchemaType = {
    "chip_addr": {
        "type": 'integer',
        "required": False,
        "empty": False,
        "default": '0x48'},
    "integration_time": {
        "required": False,
        "empty": False,
        "allowed": [13.7, 101, 402],
        "default": 101,
    },
    "gain": {
        "required": False,
        "empty": False,
        "allowed": [1, 16],
        "default": 1,
    },
}


class Sensor(GenericSensor):
    """
    Implementation of Sensor class for the Adafruit_ADS1x15.
    """

    SENSOR_SCHEMA: CerberusSchemaType = {
        "type": {
            "type": 'string',
            "required": False,
            "empty": False,
            "allowed": ['broadband', 'infrared', 'lux'],
            "default": 'lux',
        },
    }

    def setup_module(self) -> None:
        # pylint: disable=import-outside-toplevel,attribute-defined-outside-init
        # pylint: disable=import-error,no-member
        import board  # type: ignore
        import busio  # type: ignore
        import adafruit_tsl2561 # type: ignore
        # Create the I2C bus
        self.i2c = busio.I2C(board.SCL, board.SDA)

        # Convert sensor address from hex to dec
        self.address = 57
        if self.config["chip_addr"] == 0x39:
            self.address = 57
        elif self.config["chip_addr"] == 0x49:
            self.address = 73
        elif self.config["chip_addr"] == 0x29:
            self.address = 41

        self.tsl = adafruit_tsl2561.TSL2561(self.i2c, self.address)

        # Set gain 0=1x, 1=16x
        if self.config["gain"] == 1:
            self.tsl.gain = 0
        elif self.config["gain"] == 16:
            self.tsl.gain = 1

        # Set integration time (0=13.7ms, 1=101ms, 2=402ms, or 3=manual)
        if self.config["integration_time"] == 13.7:
            self.tsl.integration_time = 0
        elif self.config["integration_time"] == 101:
            self.tsl.integration_time = 1
        elif self.config["integration_time"] == 402:
            self.tsl.integration_time = 2

        self.tsl.enabled = True

        #print("tsl2561 Enabled = {}".format(self.tsl.enabled))
        #print("tsl2561 Gain = {}".format(self.tsl.gain))
        #print("tsl2561 Integration time = {}".format(self.tsl.integration_time))

    def get_value(self, sens_conf: ConfigType) -> SensorValueType:
        # pylint: disable=import-outside-toplevel,attribute-defined-outside-init
        # pylint: disable=import-error,no-member
        import time

        self.tsl.enabled = True
        time.sleep(1)

        sens_type = sens_conf["type"]
        data = {
            "broadband": self.tsl.broadband,
            "infrared": self.tsl.infrared,
            "lux": self.tsl.lux
        }

        self.tsl.enabled = False

        if data[sens_type] is None: # Possible sensor underrange or overrange.
            data[sens_type] = -1

        return cast(
            float,
            data[sens_type],
        )
