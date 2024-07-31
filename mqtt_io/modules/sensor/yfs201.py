"""

YF-S201 Flow Rate Sensor

Example configuration:

sensor_modules:
  - name: yfs201
    module: yfs201

sensor_inputs:
  - name: flow_rate1
    module: yfs201
    pin: 0
    digits: 0
    interval: 10
"""

from typing import Dict
from ...types import CerberusSchemaType, ConfigType, SensorValueType
from . import GenericSensor

REQUIREMENTS = ("gpiozero",)


class YFS201:
    """
    YF-S201 Flow Rate Sensor class
    Multiple instances support multiple sensors on different pins
    """

    def __init__(self, gpiozero, name: str, pin: int) -> None: # type: ignore[no-untyped-def]
        self.name = name
        self.pin = gpiozero.DigitalInputDevice(pin)
        self.pin.when_activated = self.count_pulse
        self.count = 0

    def count_pulse(self) -> None:
        """Increment pulse count."""
        self.count += 1

    def reset_count(self) -> None:
        """Reset pulse count."""
        self.count = 0

    def flow_rate(self, sample_window: int) -> float:
        """Return flow rate in liters per minute.

        From YF-S201 manual:
        Pluse Characteristic:F=7Q(L/MIN).
        2L/MIN=16HZ 4L/MIN=32.5HZ 6L/MIN=49.3HZ 8L/MIN=65.5HZ 10L/MIN=82HZ

        Pulse frequency (Hz) / 7.0 = flow rate in L/min

        sample_window is in seconds, so hz is pulse_count / sample_window
        """
        hertz = self.count / sample_window
        return hertz / 7.0

    def get_value(self, interval: int) -> float:
        """Return flow rate in L/min over interval seconds and reset count."""
        flow_rate = self.flow_rate(interval)
        self.reset_count()
        return flow_rate


class Sensor(GenericSensor):
    """
    YF-S201 Flow Rate Sensor
    """

    SENSOR_SCHEMA: CerberusSchemaType = {
        "pin": {
            "type": 'integer',
            "required": True,
            "empty": False,
        }
    }

    def setup_module(self) -> None:
        # pylint: disable=import-outside-toplevel,import-error
        import gpiozero  # type: ignore

        self.gpiozero = gpiozero
        self.sensors: Dict[str, YFS201] = {}

    def setup_sensor(self, sens_conf: ConfigType) -> None:
        sensor = YFS201(
            gpiozero=self.gpiozero, name=sens_conf["name"], pin=sens_conf["pin"]
        )
        self.sensors[sensor.name] = sensor

    def get_value(self, sens_conf: ConfigType) -> SensorValueType:
        return self.sensors[sens_conf["name"]].get_value(sens_conf["interval"])
