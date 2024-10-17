"""
AS3935 Ligntning Sensor

Example configuration:

sensor_modules:
  - name: AS3935_Sensor
    module: as3935
    pin: 17
    auto_filter: True
    indoor: True

sensor_inputs:
  - name: distance
    module: AS3935_Sensor
    digits: 4
    interval: 5
    type: distance

Module Options
--------------
See also:
https://www.embeddedadventures.com/datasheets/AS3935_Datasheet_EN_v2.pdf
https://github.com/fourstix/Sparkfun_CircuitPython_QwiicAS3935/blob/master/sparkfun_qwiicas3935.py
https://github.com/fourstix/Sparkfun_CircuitPython_QwiicAS3935/blob/master/examples

pin:                 Interrupt GPIO Pin
auto_filter:         Set noise_level, mask_disturber and watchdog_threshold automatically.
                     Default: True
indoor:              Set whether or not the sensor should use an indoor configuration.
                     Default: True
lightning_threshold: number of lightning detections required before an
                     interrupt is raised.
                     Default: 1
watchdog_threshold:  This function returns the threshold for events that trigger the IRQ
                     Pin. Only sensitivity threshold values 1 to 10 allowed.
                     Default: 2
spike_rejection:     This setting, like the watchdog threshold, can help determine
                     between false events and actual lightning. The shape of the spike is
                     analyzed during the chip's signal validation routine. Increasing this
                     value increases robustness at the cost of sensitivity to distant
                     events.
                     Default: 2
noise_level:         The noise floor level is compared to a known reference voltage. If
                     this level is exceeded the chip will issue an interrupt to the IRQ pin,
                     broadcasting that it can not operate properly due to noise (INT_NH).
                     Check datasheet for specific noise level tolerances when setting this
                     register.
                     Default: 2
mask_disturber       Setting this True or False will change whether or not disturbers
                     trigger the IRQ pin.
                     Default: False
division_ratio:      The antenna is designed to resonate at 500kHz and so can be tuned
                     with the following setting. The accuracy of the antenna must be within
                     3.5 percent of that value for proper signal validation and distance
                     estimation. The division ratio can only be set to 16, 32, 64 or 128.
                     Default: 16
tune_cap:            This setting will add capacitance to the series RLC antenna on the
                     product. It's possible to add 0-120pF in steps of  8pF to the antenna.
                     The Tuning Cap value will be set between 0 and 120pF, in steps of 8pF.
                     If necessary, the input value is rounded down to the nearest 8pF.
                     Default: 0

Sensor Options
--------------

type:                The following types are supported:
                     last:      last lightning in unix timestamp format
                     distance:  distance of last lightning in km
                     energy:    energy of last lightning (no unit, no physical meaning)
                     number:    number of lightning events since start

"""
# pylint: disable=line-too-long
# pylint: disable=too-many-branches
# pylint: disable=too-many-statements

import logging
from typing import Dict
from ...types import CerberusSchemaType, ConfigType, SensorValueType
from . import GenericSensor

_LOG = logging.getLogger(__name__)

REQUIREMENTS = ("gpiozero","sparkfun_qwiicas3935")

CONFIG_SCHEMA: CerberusSchemaType = {
    "pin": {
        "type": 'integer',
        "required": True,
        "empty": False
    },
    "lightning_threshold": {
        "type": 'integer',
        "required": False,
        "empty": False,
        "allowed": [1, 5, 9, 16],
        "default": 1,
    },
    "watchdog_threshold": {
        "type": 'integer',
        "required": False,
        "empty": False,
        "min": 1,
        "max": 10,
        "default": 2,
    },
    "spike_rejection": {
        "type": 'integer',
        "required": False,
        "empty": False,
        "min": 1,
        "max": 11,
        "default": 2,
    },
    "noise_level": {
        "type": 'integer',
        "required": False,
        "empty": False,
        "min": 1,
        "max": 7,
        "default": 2,
    },
    "mask_disturber": {
        "type": 'boolean',
        "required": False,
        "empty": False,
        "default": False,
    },
    "auto_filter": {
        "type": 'boolean',
        "required": False,
        "empty": False,
        "default": True,
    },
    "indoor": {
        "type": 'boolean',
        "required": False,
        "empty": False,
        "default": True,
    },
    "division_ratio": {
        "type": 'integer',
        "required": False,
        "empty": False,
        "allowed": [16, 32, 64, 128],
        "default": 16,
    },
    "tune_cap": {
        "type": 'integer',
        "required": False,
        "empty": False,
        "min": 0,
        "max": 120,
        "default": 0,
    },
}


class FRANKLINSENSOR:
    """
    Franklin Sensor class
    """

    def __init__(self, gpiozero, lightning, name: str, pin: int) -> None:  # type: ignore[no-untyped-def]
        self.name = name
        self.pin = gpiozero.DigitalInputDevice(pin)
        self.pin.when_activated = self.trigger_interrupt
        self.lightning = lightning
        self.count = 0
        self.data = {
            "last": int(0),
            "distance": float(0),
            "energy": float(0),
            "number": int(0)
        }

    def trigger_interrupt(self) -> None:
        """ When the interrupt goes high """
        # pylint: disable=import-outside-toplevel,attribute-defined-outside-init
        # pylint: disable=import-error,no-member
        import time # type: ignore
        time.sleep(0.05)
        _LOG.debug("as3935: Interrupt called!")
        interrupt_value = self.lightning.read_interrupt_register()
        if interrupt_value == self.lightning.NOISE:
            _LOG.debug("as3935: Noise detected.")
            if self.lightning.AUTOFILTER is True:
                self.reduce_noise()
        elif interrupt_value == self.lightning.DISTURBER:
            _LOG.debug("as3935: Disturber detected.")
            if self.lightning.AUTOFILTER is True:
                self.increase_threshold()
        elif interrupt_value == self.lightning.LIGHTNING:
            _LOG.debug("as3935: Lightning strike detected!")
            _LOG.debug("as3935: Approximately: %s km away!", self.lightning.distance_to_storm)
            _LOG.debug("as3935: Energy value: %s", self.lightning.lightning_energy)
            self.count += 1
            now = time.time()
            self.data = {
                "last": int(now),
                "distance": float(self.lightning.distance_to_storm),
                "energy": float(self.lightning.lightning_energy),
                "number": int(self.count)
            }

    def reduce_noise(self) -> None:
        """ Reduce Noise Level """
        value = self.lightning.noise_level
        value += 1
        if value > 7:
            _LOG.debug("as3935: Noise floor is at the maximum value 7.")
            return
        _LOG.debug("as3935: Increasing the noise event threshold to %s", value)
        self.lightning.noise_level = value

    def increase_threshold(self) -> None:
        """ Increase Watchdog Threshold """
        value = self.lightning.watchdog_threshold
        value += 1
        if value > 10:
            self.lightning.mask_disturber = True
            _LOG.debug("as3935: Watchdog threshold is at the maximum value 10. Mask disturbers now.")
            return
        _LOG.debug("as3935: Increasing the disturber watchdog threshold to %s", value)
        self.lightning.watchdog_threshold = value

    def get_value(self, value: str) -> float:
        """ Return the value of 'type' """
        ret = float(self.data[value])
        return ret


class Sensor(GenericSensor):
    """
    Flowsensor: Flow Rate Sensor
    """

    SENSOR_SCHEMA: CerberusSchemaType = {
        "type": {
            "type": 'string',
            "required": False,
            "empty": False,
            "allowed": ['last', 'distance', 'energy', 'number'],
            "default": 'distance',
        },
    }

    def setup_module(self) -> None:
        # pylint: disable=import-outside-toplevel,attribute-defined-outside-init
        # pylint: disable=import-error,no-member
        import board  # type: ignore
        import sparkfun_qwiicas3935 # type: ignore
        import gpiozero  # type: ignore

        # Create gpio object
        self.gpiozero = gpiozero
        self.sensors: Dict[str, FRANKLINSENSOR] = {}

        # Create bus object using our board's I2C port
        self.i2c = board.I2C()

        # Create as3935 object
        self.lightning = sparkfun_qwiicas3935.Sparkfun_QwiicAS3935_I2C(self.i2c)

        if self.lightning.connected:
            _LOG.debug("as3935: Schmow-ZoW, Lightning Detector Ready!")
        else:
            _LOG.debug("as3935: Lightning Detector does not appear to be connected. Please check wiring.")

        # Set defaults
        self.lightning.clear_statistics()
        self.lightning.reset()
        self.lightning.watchdog_threshold = 2
        self.lightning.noise_level = 2
        self.lightning.mask_disturber = False
        self.lightning.spike_rejection = 2
        self.lightning.lightning_threshold = 1
        self.lightning.division_ratio = 16
        self.lightning.tune_cap = 0
        self.lightning.indoor_outdoor = self.lightning.INDOOR
        self.lightning.mask_disturber = False
        self.lightning.AUTOFILTER = True # Our own var

        # Auto Filter False-Positives?
        if 'auto_filter' in self.config:
            self.lightning.AUTOFILTER=self.config["auto_filter"]

        # Lightning Threashold
        if 'lightning_threshold' in self.config:
            self.lightning.lightning_threshold = self.config["lightning_threshold"]

        # Watchdog Threashold
        if 'watchdog_threshold' in self.config:
            self.lightning.watchdog_threshold = self.config["watchdog_threshold"]

        # Spike Rejection
        if 'spike_rejection' in self.config:
            self.lightning.spike_rejection = self.config["spike_rejection"]

        # Noise Floor / Level
        if 'noise_level' in self.config:
            self.lightning.noise_level = self.config["noise_level"]

        # Mask Disturber
        if 'mask_disturber' in self.config:
            self.lightning.mask_disturber = self.config["mask_disturber"]

        # Indoor/Outdoor
        if 'indoor' in self.config:
            if self.config["indoor"] is True:
                self.lightning.indoor_outdoor = self.lightning.INDOOR
            else:
                self.lightning.indoor_outdoor = self.lightning.OUTDOOR

        # Division Ratio
        if 'division_ratio' in self.config:
            self.lightning.division_ratio = self.config["division_ratio"]

        # Tune Cap
        if 'tune_cap' in self.config:
            self.lightning.tune_cap = self.config["tune_cap"]

        # Debug
        _LOG.debug("as3935: The noise floor is %s", self.lightning.noise_level)
        _LOG.debug("as3935: The disturber watchdog threshold is %s", self.lightning.watchdog_threshold)
        _LOG.debug("as3935: The Lightning Detectori's Indoor/Outdoor mode is set to: %s", self.lightning.indoor_outdoor)
        _LOG.debug("as3935: Are disturbers being masked? %s", self.lightning.mask_disturber)
        _LOG.debug("as3935: Spike Rejection is set to: %s", self.lightning.spike_rejection)
        _LOG.debug("as3935: Division Ratio is set to: %s", self.lightning.division_ratio)
        _LOG.debug("as3935: Internal Capacitor is set to: %s", self.lightning.tune_cap)

        # Create sensor
        sensor = FRANKLINSENSOR(
            gpiozero=self.gpiozero, lightning=self.lightning, name=self.config["name"], pin=self.config["pin"]
        )
        self.sensors[sensor.name] = sensor

    def get_value(self, sens_conf: ConfigType) -> SensorValueType:
        return self.sensors[self.config["name"]].get_value(
            sens_conf["type"]
        )
