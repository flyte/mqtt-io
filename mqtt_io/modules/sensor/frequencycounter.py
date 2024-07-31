"""

Frequencycounter: Generic Frequency Counter

Example configuration:

sensor_modules:
  - name: frequency
    module: frequencycounter

sensor_inputs:
  - name: flow_rate1
    module: frequency
    pin: 0
    digits: 0
    interval: 10

"""

from typing import Dict
from ...types import CerberusSchemaType, ConfigType, SensorValueType
from . import GenericSensor

REQUIREMENTS = ("gpiozero",)


class FREQUENCYCOUNTER:
    """
    Frequency Counter class
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

    def frequency(self, sample_window: int) -> float:
        """
        sample_window is in seconds, so hz is pulse_count / sample_window
        """
        hertz = self.count / sample_window
        return hertz

    def get_value(self, interval: int) -> float:
        """Return frequency over interval seconds and reset count."""
        frequency = self.frequency(interval)
        self.reset_count()
        return frequency


class Sensor(GenericSensor):
    """
    Frequency Counter
    """

    SENSOR_SCHEMA: CerberusSchemaType = {
        "pin": {
            "type": 'integer',
            "required": True,
            "empty": False,
        },
        "interval": {
            "type": 'integer',
            "required": True,
            "empty": False,
        }
    }

    def setup_module(self) -> None:
        # pylint: disable=import-outside-toplevel,import-error
        import gpiozero  # type: ignore

        self.gpiozero = gpiozero
        self.sensors: Dict[str, FREQUENCYCOUNTER] = {}

    def setup_sensor(self, sens_conf: ConfigType) -> None:
        sensor = FREQUENCYCOUNTER(
            gpiozero=self.gpiozero, name=sens_conf["name"], pin=sens_conf["pin"]
        )
        self.sensors[sensor.name] = sensor

    def get_value(self, sens_conf: ConfigType) -> SensorValueType:
        return self.sensors[sens_conf["name"]].get_value(sens_conf["interval"])
