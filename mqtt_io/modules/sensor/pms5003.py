"""
PMS5003 Particulate Matter Sensor
"""

import time
from typing import cast
from ...types import CerberusSchemaType, ConfigType, SensorValueType
from . import GenericSensor

REQUIREMENTS = ("plantower",)
CONFIG_SCHEMA: CerberusSchemaType = {
    "serial_port": {"type": 'string', "required": True, "empty": False},
}


class Sensor(GenericSensor):
    """
    Implementation of Sensor class for the PMS5003 sensor.
    """

    SENSOR_SCHEMA: CerberusSchemaType = {
        "type": {
            "type": 'string',
            "required": False,
            "empty": False,
            "default": 'pm25_std',
            "allowed": 
                ['pm10_cf1', 'pm25_cf1','pm100_cf1',
                 'pm10_std','pm25_std','pm100_std',
                 'gr03um','gr05um','gr10um',
                 'gr25um','gr50um','gr100um'],
        }
    }

    def setup_module(self) -> None:
        # pylint: disable=import-outside-toplevel,import-error
        import plantower # type: ignore

        self.serial_port = self.config["serial_port"]
        self.sensor = plantower.Plantower(port=self.serial_port)
        self.sensor.mode_change(plantower.PMS_PASSIVE_MODE)
        self.sensor.set_to_wakeup()
        time.sleep(30) #give fan time to stabilize readings

    def get_value(self, sens_conf: ConfigType) -> SensorValueType:
        """
        Get the particulate data from the sensor
        """
        #turn sensor off if interval between readings is >= 2 minutes
        sleep_sensor = sens_conf["interval"] >= 120
        if sleep_sensor:
            self.sensor.set_to_wakeup()
            time.sleep(30)
        sens_type = sens_conf["type"]
        result = self.sensor.read()
        if sleep_sensor:
            self.sensor.set_to_sleep()
        return cast(
            int,
            {
                "pm10_cf1": result.pm10_cf1,
                "pm25_cf1": result.pm25_cf1,
                "pm100_cf1": result.pm100_cf1,
                "pm10_std": result.pm10_std,
                "pm25_std": result.pm25_std,
                "pm100_std": result.pm100_std,
                "gr03um": result.gr03um,
                "gr05um": result.gr05um,
                "gr10um": result.gr10um,
                "gr25um": result.gr25um,
                "gr50um": result.gr50um,
                "gr100u": result.gr100um
                }[sens_type],
        )

    def cleanup(self) -> None:
        self.sensor.set_to_sleep()
