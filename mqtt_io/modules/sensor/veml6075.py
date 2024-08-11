"""
VEML 6075 UV sensor
"""

from mqtt_io.types import ConfigType, SensorValueType
from . import GenericSensor
import logging
import time

REQUIREMENTS = ("smbus2", "veml6075",)

CONFIG_SCHEMA = {
    "i2c_bus_num": {"type": "integer", "required": True, "empty": False},
}


# UV COEFFICIENTS AND RESPONSIVITY
# See https://web.archive.org/web/20190416120825/http://www.vishay.com/docs/84339/designingveml6075.pdf
# For more details
##################################################################################
# Configuration                #  a   #   b  #  c   #  d  #  UVAresp  # UVBresp  #
##################################################################################
# No teflon (open air)         # 2.22 # 1.33 # 2.95 # 1.74 # 0.001461 # 0.002591 #
# 0.1 mm teflon 4.5 mm window  # 2.22 # 1.33 # 2.95 # 1.74 # 0.002303 # 0.004686 #
# 0.1 mm teflon 5.5 mm window  # 2.22 # 1.33 # 2.95 # 1.74 # 0.002216 # 0.005188 #
# 0.1 mm teflon 10 mm window   # 2.22 # 1.33 # 2.95 # 1.74 # 0.002681 # 0.004875 #
# 0.25 mm teflon 10 mm window  # 2.22 # 1.33 # 2.95 # 1.74 # 0.002919 # 0.009389 #
# 0.4 mm teflon 10 mm window   # 2.22 # 1.17 # 2.95 # 1.58 # 0.004770 # 0.006135 #
# 0.7 mm teflon 10 mm window   # 2.22 # 1.17 # 2.95 # 1.58 # 0.007923 # 0.008334 #
# 1.0 mm teflon 5.5 mm window  # 2.55 # 1.00 # 3.80 # 1.10 # 0.006000 # 0.003100 #
##################################################################################

_LOG = logging.getLogger(__name__)


class Sensor(GenericSensor):
    """
    Implementation of Sensor class for the VEML 6075 UV sensor.
    """

    SENSOR_SCHEMA = {
        "a": {"type": "float", "required": False, "empty": False, "default": 2.22},
        "b": {"type": "float", "required": False, "empty": False, "default": 1.33},
        "c": {"type": "float", "required": False, "empty": False, "default": 2.95},
        "d": {"type": "float", "required": False, "empty": False, "default": 1.74},
        "UVAresp": {"type": "float", "required": False, "empty": False, "default": 0.001461},
        "UVBresp": {"type": "float", "required": False, "empty": False, "default": 0.002591},
    }
    
    def setup_module(self) -> None:
        # pylint: disable=import-outside-toplevel,import-error
        from smbus2 import SMBus  # type: ignore
        from veml6075 import VEML6075  # type: ignore

        self.bus = SMBus(self.config["i2c_bus_num"])
        self.sensor = VEML6075(i2c_dev=self.bus)
        self.sensor.set_shutdown(True)
        self.sensor.set_high_dynamic_range(False)
        self.sensor.set_integration_time('100ms')
        self.sensor.set_shutdown(False)


    def calculate_uv_index(self, sens_conf, uva, uvb, uv_comp1, uv_comp2) -> float:
        _LOG.info("UVA: " + str(uva) + " UVB: " + str(uvb) + " UV_comp1: " + str(uv_comp1) + " UV_comp2: " + str(uv_comp2))
        uva_calc = uva - (sens_conf["a"] * uv_comp1) - (sens_conf["b"] * uv_comp2)
        _LOG.info("uva_calc " + str(uva_calc))
        uvb_calc = uvb - (sens_conf["c"] * uv_comp1) - (sens_conf["d"] * uv_comp2)
        _LOG.info("uvb_calc " + str(uvb_calc))
        uva_index = uva_calc * sens_conf["UVAresp"]
        _LOG.info("uva_index " + str(uva_index))
        uvb_index = uvb_calc * sens_conf["UVBresp"]
        _LOG.info("uvb_index " + str(uvb_index))
        uv_index = (uva_index + uvb_index) / 2
        return uv_index

    def get_value(self, sens_conf: ConfigType) -> SensorValueType:
        """
        Get the UV index from the sensor
        """
        # Setup and turn on the sensor

        # Fetch the values
        #time.sleep(.2)
        uva, uvb = self.sensor.get_measurements()
        uv_comp1, uv_comp2 = self.sensor.get_comparitor_readings()

        # Turn off the sensor
        #self.sensor.set_shutdown(True)

        # Calculate and return the UV index
        return self.calculate_uv_index(sens_conf, uva, uvb, uv_comp1, uv_comp2)
