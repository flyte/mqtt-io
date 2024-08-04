"""
DFRobot Gravity DFR0300 Electrical Conductivity Sensor
"""

import abc
import json
import logging
import os
import time

from typing import cast

from mqtt_io.events import EventBus, SensorReadEvent
from mqtt_io.exceptions import RuntimeConfigError

from ...types import CerberusSchemaType, ConfigType, PinType, SensorValueType
from . import GenericSensor

_LOG = logging.getLogger(__name__)


CONFIG_SCHEMA: CerberusSchemaType = {
    "i2c_bus_num": {"type": "integer", "required": False, "empty": False, "default": 1},
    "chip_addr": {
        "type": "integer",
        "required": False,
        "empty": False,
        "default": 0x10,
    },
}

ANALOG_PINS = [0, 1, 2, 3]
CALIBRATION_FILE = "ec_config.json"
CALIBRATION_FILE_ENCODING = "ascii"
DEFAULT_TEMPERATURE = 25.0
INITIAL_KVALUE = 1.0
TEMPSENSOR_ID = "tempsensor"


def calc_raw_ec(voltage: float) -> float:
    """Convert voltage to raw EC"""
    return 1000 * voltage / 820.0 / 200.0


class Calibrator(abc.ABC):
    """Class to handle calibration"""

    def __init__(self) -> None:
        self.kvalue_low = INITIAL_KVALUE
        self.kvalue_mid = INITIAL_KVALUE
        self.kvalue_high = INITIAL_KVALUE
        if os.path.exists(CALIBRATION_FILE):
            self.kvalue_low, self.kvalue_mid, self.kvalue_high = self.read_calibration()

    def calibrate(self, voltage, temperature) -> None:
        """Set the calibration values and write out to file."""

        def calc_kvalue(ec_solution, voltage, temperature):
            comp_ec_solution = ec_solution * (1.0 + 0.0185 * (temperature - 25.0))
            return round(820.0 * 200.0 * comp_ec_solution / 1000.0 / voltage, 2)

        raw_ec = calc_raw_ec(voltage)
        if 0.9 < raw_ec < 1.9:
            self.kvalue_low = calc_kvalue(1.413, voltage, temperature)
            _LOG.info(">>>Buffer Solution:1.413us/cm kvalue_low: %f", self.kvalue_low)
        elif 1.9 <= raw_ec < 4:
            self.kvalue_mid = calc_kvalue(2.8, voltage, temperature)
            _LOG.info(">>>EC:2.8ms/cm kvalue_mid: %f", self.kvalue_mid)
        elif 9 < raw_ec < 16.8:
            self.kvalue_high = calc_kvalue(12.88, voltage, temperature)
            _LOG.info(">>>Buffer Solution:12.88ms/cm kvalue_high:%f ", self.kvalue_high)
        else:
            raise ValueError(">>>Buffer Solution Error Try Again<<<")

        # Should think about looping to stabalise the reading before writing
        self.write_calibration()

    def read_calibration(self):
        """Read calibrated values from json file.
        {
          "kvalue_low": 1.0,
          "kvalue_mid": 1.0,
          "kvalue_high": 1.0
        }

        """
        if os.path.exists(CALIBRATION_FILE):
            with open(CALIBRATION_FILE, "r", encoding=CALIBRATION_FILE_ENCODING) as f:
                data = json.load(f)
                kvalue_low = float(data["kvalue_low"])
                kvalue_mid = float(data["kvalue_mid"])
                kvalue_high = float(data["kvalue_high"])
            return (kvalue_low, kvalue_mid, kvalue_high)
        raise FileNotFoundError(f"Calibration file ${CALIBRATION_FILE} not found")

    def write_calibration(self):
        """Write calibrated values to json file."""
        try:
            with open(CALIBRATION_FILE, "w", encoding=CALIBRATION_FILE_ENCODING) as f:
                data = {
                    "kvalue_low": self.kvalue_low,
                    "kvalue_mid": self.kvalue_mid,
                    "kvalue_high": self.kvalue_high,
                }
                json.dump(data, f, indent=2, encoding="ascii")
        except IOError as exc:
            _LOG.warning("Failed to write calibration data: %s", exc)


class Sensor(GenericSensor):
    """
    Implementation of Sensor class for the DFR0300 Electrical Conductivity Sensor

    """

    SENSOR_SCHEMA: CerberusSchemaType = {
        "pin": {
            "type": "integer",
            "required": True,
            "empty": False,
            "allowed": ANALOG_PINS,
        },
        TEMPSENSOR_ID: {
            "type": "string",
            "required": False,
            "empty": False,
        },
    }

    def setup_module(self) -> None:
        # pylint: disable=import-outside-toplevel,import-error
        from .drivers.DFRobot_RaspberryPi_Expansion_Board import DFRobotExpansionBoardIIC  # type: ignore

        self.board = DFRobotExpansionBoardIIC(
            self.config["i2c_bus_num"], self.config["chip_addr"]
        )  # type: ignore
        self.board.setup()

        self.board.set_adc_enable()
        self.pin2channel = {
            0: self.board.A0,
            1: self.board.A1,
            2: self.board.A2,
            3: self.board.A3,
        }

        self.kvalue = INITIAL_KVALUE
        calibrator = Calibrator()
        self.kvalue_low = calibrator.kvalue_low
        self.kvalue_mid = calibrator.kvalue_mid
        self.kvalue_high = calibrator.kvalue_high

    def setup_sensor(self, sens_conf: ConfigType, event_bus: EventBus) -> None:
        """
        Setup the sensor module
        """
        # pylint: disable=attribute-defined-outside-init
        self.temperature = DEFAULT_TEMPERATURE

        pin: PinType = sens_conf["pin"]
        try:
            self.channel = self.pin2channel[pin]
        except KeyError as exc:
            raise RuntimeConfigError(
                "pin '%s' was not configured to return a valid value" % pin
            ) from exc

        if TEMPSENSOR_ID not in sens_conf:
            _LOG.info("dfr0300: No temperature sensor configured")
            return

        def on_sensor_read(data):
            """Callback for sensor read event"""
            _LOG.info("Sensor read event cb %s", dir(data))
            if data.sensor_name == sens_conf[TEMPSENSOR_ID] and data.value is not None:
                self.temperature = data.value

        self.event_bus = event_bus
        self.event_bus.subscribe(SensorReadEvent, on_sensor_read)

    def ec_from_voltage(self, voltage, temperature):
        """Convert voltage to EC with temperature compensation"""
        # pylint: disable=attribute-defined-outside-init
        raw_ec = calc_raw_ec(voltage)
        value_temp = raw_ec * self.kvalue
        if value_temp > 5.0:
            self.kvalue = self.kvalue_high
        elif value_temp >= 2.0:
            self.kvalue = self.kvalue_mid
        elif value_temp < 2.0:
            self.kvalue = self.kvalue_low
        value = raw_ec * self.kvalue
        return value / (1.0 + 0.0185 * (temperature - 25.0))

    def get_value(self, _sens_conf: ConfigType) -> SensorValueType:
        """
        Get the EC from the sensor
        """
        voltage = self.board.get_adc_value(self.channel)
        ec = self.ec_from_voltage(voltage, self.temperature)
        _LOG.info("Temperature:%.1f ^C EC:%.2f ms/cm", self.temperature, ec)
        return cast(
            float,
            ec,
        )
