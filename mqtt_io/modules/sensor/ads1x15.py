"""
ADS1x15 analog to digital converters
"""

from typing import cast

from ...types import CerberusSchemaType, ConfigType, SensorValueType
from . import GenericSensor

SENSOR_ADS1015 = "ADS1015"
SENSOR_ADS1115 = "ADS1115"
SENSOR_TYPES = [SENSOR_ADS1015, SENSOR_ADS1115]

REQUIREMENTS = ("adafruit-circuitpython-ads1x15",)
CONFIG_SCHEMA: CerberusSchemaType = {
    "chip_addr": dict(type="integer", required=False, empty=False, default=0x48),
    "type": dict(
        type="string",
        required=True,
        empty=False,
        allowed=SENSOR_TYPES,
    ),
    "pin": dict(type="integer", required=True, empty=False, allowed=[0, 1, 2, 3]),
    "gain": dict(
        type="integer",
        required=False,
        empty=False,
        allowed=[2 / 3, 1, 2, 4, 8, 16],
        default=1,
    ),
}


class Sensor(GenericSensor):
    """
    Implementation of Sensor class for the Adafruit_ADS1x15.
    """

    SENSOR_SCHEMA: CerberusSchemaType = {
        "type": dict(
            type="string",
            required=False,
            empty=False,
            allowed=["value", "voltage"],
            default="value",
        ),
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

        # Create single-ended input on channel 0
        self.chan = AnalogIn(self.ads, self.config["pin"])

    def get_value(self, sens_conf: ConfigType) -> SensorValueType:
        """
        Get the value or voltage from the sensor
        """
        sens_type = sens_conf["type"]
        data = dict(value=self.chan.value, voltage=self.chan.voltage)
        return cast(
            float,
            data[sens_type],
        )
