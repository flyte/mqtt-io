"""
INA219 DC current sensor

Mandatory:
- chip_addr
- shunt_ohms
Optional, for more precision:
- amps (Maximum ampere you expect)
- range (16 or 32) -> Will be the maximum voltage you want to measure
- gain (40, 80, 160 or 320) -> maximum shunt voltage (milli volt)
Optional:
- low_power: send ina219 to sleep between readings

Output:
- power (in watt)
- current (in ampere)
- bus_voltage (in volt)
- shunt_voltage (in milli volt)
"""

from json import dumps
from typing import cast

from ...types import CerberusSchemaType, ConfigType, SensorValueType
from . import GenericSensor

REQUIREMENTS = ("pi-ina219",)
CONFIG_SCHEMA: CerberusSchemaType = {
    "chip_addr": dict(type="integer", required=True, empty=False),
    "shunt_ohms": dict(type="float", required=False, empty=False),
    "amps": dict(type="float", required=False, empty=False),
    "range": dict(type="integer", required=False, empty=False),
    "gain": dict(type="integer", required=False, empty=False),
    "low_power": dict(type="boolean", required=False, empty=False),
}


class Sensor(GenericSensor):
    """
    Implementation of Sensor class for the INA219 sensor.
    """

    SENSOR_SCHEMA: CerberusSchemaType = {
        "type": dict(
            type="string",
            required=False,
            empty=False,
            default="power",
            allowed=["all", "power", "current", "bus_voltage", "shunt_voltage"],
        )
    }

    def setup_module(self) -> None:
        # pylint: disable=import-outside-toplevel,attribute-defined-outside-init
        # pylint: disable=import-error,no-member
        from ina219 import INA219, DeviceRangeError  # type: ignore

        self.i2c_addr: int = self.config["chip_addr"]

        if "shunt_ohms" in self.config:
            shunt_ohms = self.config["shunt_ohms"]
        else:
            shunt_ohms = 100

        if "amps" in self.config:
            self.ina = INA219(shunt_ohms, self.config["amps"], address=self.i2c_addr)
        else:
            self.ina = INA219(shunt_ohms, address=self.i2c_addr)

        ## Configure ina sensor with range and gain from config or default
        if "range" in self.config:
            if self.config["range"] <= 16:
                range = self.ina.RANGE_16V
            else:
                range = self.ina.RANGE_32V
        else:
            range = self.ina.RANGE_32V
        if "gain" in self.config:
            if self.config["gain"] == 40:
                gain = self.ina.GAIN_1_40MV
            elif self.config["gain"] == 80:
                gain = self.ina.GAIN_2_80MV
            elif self.config["gain"] == 160:
                gain = self.ina.GAIN_4_160MV
            elif self.config["gain"] == 320:
                gain = self.ina.GAIN_8_320MV
            else:
                gain = self.ina.GAIN_AUTO
        else:
            gain = self.ina.GAIN_AUTO
        self.ina.configure(range, gain)

    def get_value(self, sens_conf: ConfigType) -> SensorValueType:
        sens_type = sens_conf["type"]

        if "low_power" in self.config and self.config["low_power"]:
            self.ina.wake()

        bus_voltage = self.ina.voltage()
        try:
            current = self.ina.current() / 1000
            power = self.ina.power() / 1000
            shunt_voltage = self.ina.shunt_voltage()
        except DeviceRangeError as e:
            # Current out of device range with specified shunt resistor
            print(e)
            return None

        all = {
            "power": power,
            "current": current,
            "bus_voltage": bus_voltage,
            "shunt_voltage": shunt_voltage,
        }

        if "low_power" in self.config and self.config["low_power"]:
            self.ina.sleep()

        return cast(
            float,
            dict(
                power=power,
                current=current,
                bus_voltage=bus_voltage,
                shunt_voltage=shunt_voltage,
                all=dumps(all),
            )[sens_type],
        )
