"""
INA219 DC current sensor
"""

# Mandatory:
# - chip_addr
# - shunt_ohms
# Optional, for more precision:
# - amps (Maximum ampere you expect)
# - range (16 or 32) -> Will be the maximum voltage you want to measure
# - gain (40, 80, 160 or 320) -> maximum shunt voltage (milli volt)
# Optional:
# - low_power: send ina219 to sleep between readings
# - i2c_bus_num: if auto detection fails - like on Pi4

# Output:
# - power (in watt)
# - current (in ampere)
# - bus_voltage (in volt)
# - shunt_voltage (in milli volt)

import logging
from typing import cast

from ...exceptions import RuntimeConfigError
from ...types import CerberusSchemaType, ConfigType, SensorValueType
from . import GenericSensor

_LOG = logging.getLogger(__name__)

REQUIREMENTS = ("pi-ina219",)
CONFIG_SCHEMA: CerberusSchemaType = {
    "chip_addr": {"type": 'integer', "required": True},
    "i2c_bus_num": {"type": 'integer', "required": False, "default": 1},
    "shunt_ohms": {"type": 'float', "required": False, "empty": False, "default": 0.1},
    "max_amps": {"type": 'float', "required": False, "empty": False},
    "voltage_range": {
        "type": 'integer',
        "required": False,
        "empty": False,
        "allowed": [16, 32],
        "default": 32
    },
    "gain": {
        "type": 'string',
        "required": False,
        "empty": False,
        "coerce": lambda x: str(x).upper(),
        "default": 'AUTO',
        "allowed": ['AUTO', '1_40MV', '2_80MV', '4_160MV', '8_320MV'],
    },
    "low_power": {"type": 'boolean', "required": False, "default": False},
}


class Sensor(GenericSensor):
    """
    Implementation of Sensor class for the INA219 sensor.
    """

    SENSOR_SCHEMA: CerberusSchemaType = {
        "type": {
            "type": 'string',
            "required": False,
            "empty": False,
            "default": 'power',
            "allowed": ['power', 'current', 'bus_voltage', 'shunt_voltage'],
        }
    }

    def setup_module(self) -> None:
        # pylint: disable=import-outside-toplevel,attribute-defined-outside-init
        # pylint: disable=import-error,no-member
        from ina219 import INA219  # type: ignore

        self.ina = INA219(
            self.config["shunt_ohms"],
            max_expected_amps=self.config.get("max_amps"),
            address=self.config["chip_addr"],
            busnum=self.config["i2c_bus_num"],
        )

        ## Configure ina sensor with range and gain from config or default
        vrange = {16: self.ina.RANGE_16V, 32: self.ina.RANGE_32V}[
            self.config["voltage_range"]
        ]
        gain = getattr(self.ina, f"GAIN_{self.config['gain']}")

        self.ina.configure(vrange, gain)

    def get_value(self, sens_conf: ConfigType) -> SensorValueType:
        # pylint: disable=import-outside-toplevel,import-error
        from ina219 import DeviceRangeError  # type: ignore

        sens_type = sens_conf["type"]

        if self.config["low_power"]:
            self.ina.wake()

        try:
            if sens_type == "power":
                return cast(float, self.ina.power()) / 1000
            if sens_type == "current":
                return cast(float, self.ina.current()) / 1000
            if sens_type == "bus_voltage":
                return cast(float, self.ina.voltage())
            if sens_type == "shunt_voltage":
                return cast(float, self.ina.shunt_voltage())
        except DeviceRangeError:
            _LOG.exception("Current out of device range with specified shunt resistor")
            return None
        finally:
            if self.config["low_power"]:
                self.ina.sleep()

        raise RuntimeConfigError(
            "ina219 sensor '%s' was not configured to return an accepted value"
            % sens_conf["name"]
        )
