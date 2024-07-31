"""
ADS1x15 analog to digital converters
"""
import threading

from typing import cast

from ...types import CerberusSchemaType, ConfigType, SensorValueType
from . import GenericSensor

SENSOR_ADS1015 = "ADS1015"
SENSOR_ADS1115 = "ADS1115"
SENSOR_TYPES = [SENSOR_ADS1015, SENSOR_ADS1115]

REQUIREMENTS = ("adafruit-circuitpython-ads1x15",)
CONFIG_SCHEMA: CerberusSchemaType = {
    "chip_addr": {"type": 'integer', "required": False, "empty": False, "default": 0x48},
    "type": {"type": 'string', "required": True, "empty": False, "allowed": SENSOR_TYPES},
    "pins": {"type": 'list', "required": True, "empty": False, "allowed": [0, 1, 2, 3]},
    "gain": {
        "required": False,
        "empty": False,
        "allowed": [0.6666666666666666, 1, 2, 4, 8, 16],
        "default": 1
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
            "allowed": ['value', 'voltage'],
            "default": 'value',
        },
        "pin": {
            "type": 'integer',
            "required": True,
            "empty": False,
            "allowed": [0, 1, 2, 3],
            "default": 0,
        },
    }

    def setup_module(self) -> None:
        # pylint: disable=import-outside-toplevel,attribute-defined-outside-init
        # pylint: disable=import-error,no-member
        import board  # type: ignore
        import busio  # type: ignore
        from adafruit_ads1x15.analog_in import AnalogIn  # type: ignore
        from adafruit_ads1x15.ads1x15 import ADS1x15  # type: ignore

        # Create the I2C bus
        self.i2c = busio.I2C(board.SCL, board.SDA)

        # Create the ADC object using the I2C bus
        if self.config["type"] == SENSOR_ADS1015:
            from adafruit_ads1x15.ads1015 import ADS1015  # type: ignore

            ad_sensor_class = ADS1015
        else:
            from adafruit_ads1x15.ads1115 import ADS1115  # type: ignore

            ad_sensor_class = ADS1115
        self.ads: ADS1x15 = ad_sensor_class(
            self.i2c, gain=self.config["gain"], address=self.config["chip_addr"]
        )

        # Create single-ended input for each pin in config
        self.channels = {pin: AnalogIn(self.ads, pin) for pin in self.config["pins"]}

        # initialize mutex lock
        self.lock = threading.Lock()

    def get_value(self, sens_conf: ConfigType) -> SensorValueType:
        """
        Get the value or voltage from the sensor
        """
        # acquire the lock
        with self.lock:
            sens_type = sens_conf["type"]
            data = {
                "value": self.channels[sens_conf['pin']].value,
                "voltage": self.channels[sens_conf['pin']].voltage,
            }

        return cast(
            float,
            data[sens_type],
        )
