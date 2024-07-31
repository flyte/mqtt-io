"""
ENS160 Air Quality Sensor

sensor_modules:
  - name: ens160
    module: ens160
    chip_addr: 0x53
    temperature_compensation: 25
    humidity_compensation: 50

sensor_inputs:
  - name: air_quality
    module: ens160
    interval: 10
    digits: 0
    type: aqi

  - name: volatile_organic_compounds
    module: ens160
    interval: 10
    digits: 0
    type: tvoc

  - name: eco2
    module: ens160
    interval: 10
    digits: 0
    type: eco2
"""

from typing import cast

from ...types import CerberusSchemaType, ConfigType
from . import GenericSensor

DEFAULT_CHIP_ADDR = 0x53
DEFAULT_TEMPERATURE_COMPENSATION = 25
DEFAULT_HUMIDITY_COMPENSATION = 50


REQUIREMENTS = ("adafruit-circuitpython-ens160",)
CONFIG_SCHEMA: CerberusSchemaType = {
    "chip_addr": {
        "type": 'integer',
        "required": False,
        "empty": False,
        "default": 'DEFAULT_CHIP_ADDR',
    },
    "temperature_compensation": {
        "type": 'float',
        "required": False,
        "empty": False,
        "default": 'DEFAULT_TEMPERATURE_COMPENSATION',
    },
    "humidity_compensation": {
        "type": 'float',
        "required": False,
        "empty": False,
        "default": 'DEFAULT_HUMIDITY_COMPENSATION',
    },
}


class Sensor(GenericSensor):
    """
    Implementation of Sensor class for the ENS160 sensor using adafruit-circuitpython-ens160.

    Mesures:
    AQI: The air quality index calculated on the basis of UBA
    Return value: 1-Excellent, 2-Good, 3-Moderate, 4-Poor, 5-Unhealthy

    TVOC: Total Volatile Organic Compounds concentration
    Return value range: 0–65000, unit: ppb

    CO2 equivalent concentration calculated according to the detected data of VOCs and hydrogen
    Return value range: 400–65000, unit: ppm

    Five levels: Excellent(400 - 600), Good(600 - 800), Moderate(800 - 1000),
                 Poor(1000 - 1500), Unhealthy(> 1500)

    NB: Need to think about how to handle the ambient_temp and relative_humidity values as
        they are currently hard-coded defaults that can be overridden by user configuration.
        Ideally these values would be read from a separate temperature/humdity sensor.
    """

    SENSOR_SCHEMA: CerberusSchemaType = {
        "type": {
            "type": 'string',
            "required": False,
            "empty": False,
            "default": 'aqi',
            "allowed": ['aqi', 'tvoc', 'eco2'],
        },
    }

    def setup_module(self) -> None:
        # pylint: disable=import-outside-toplevel,import-error
        import adafruit_ens160  # type: ignore
        import board  # type: ignore

        self.adafruit_ens160_module = adafruit_ens160
        i2c = board.I2C()  # uses board.SCL and board.SDA
        self.ens160 = adafruit_ens160.ENS160(i2c, address=self.config["chip_addr"])
        self.ens160.temperature_compensation = self.config["temperature_compensation"]
        self.ens160.humidity_compensation = self.config["humidity_compensation"]

    def get_value(self, sens_conf: ConfigType) -> float:
        """Return the sensor value in the configured type."""

        # data_validity  values:
        # NORMAL_OP - Normal operation,
        # WARM_UP - Warm-Up phase, first 3 minutes after power-on.
        # START_UP - Initial Start-Up phase, first full hour of operation after initial power-on.
        #             Only once in the sensor’s lifetime.
        # INVALID_OUT - Invalid output
        # note: Note that the status will only be stored in the non-volatile memory after an initial
        #       24h of continuous operation. If unpowered before conclusion of said period, the
        #       ENS160 will resume "Initial Start-up" mode after re-powering.
        if self.ens160.data_validity == self.adafruit_ens160_module.INVALID_OUT:
            raise RuntimeError("ENS160 sensor is returning invalid output")

        sens_type = sens_conf["type"]
        return cast(
            int,
            {"aqi": self.ens160.AQI, "tvoc": self.ens160.TVOC, "eco2": self.ens160.eCO2}[
                sens_type
            ],
        )
