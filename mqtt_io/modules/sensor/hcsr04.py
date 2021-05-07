"""
HCSR04 ultrasonic range sensor (connected to the Raspberry Pi on-board GPIO)
"""

import time
from statistics import mean
from typing import Any, Dict, List, Optional

from ...types import CerberusSchemaType, ConfigType, SensorValueType
from . import GenericSensor

REQUIREMENTS = ("RPi.GPIO",)

# HC-SR04 ultrasonic sensor_inputs
# for use at Raspberry Pi, the ECHO signal of the sensor must be reduced to 3.3V, since
# the sensor works with 5V!!
# You can simply reduce with a 3.9kOhm and 6.8kOhm resistor voltage reduction
#
# further information at http://www.netzmafia.de/skripten/hardware/RasPi/Projekt-Ultraschall/
# The code is based on the sample code of this webpage by Prof.Plate / University of Munich

# duration trigger pulse
PULSE = 0.00001
# sonic speed/2
SPEED_2 = 34300 / 2


class HCSR04:
    """
    Separate class for the distance sensors themselves, since there may be more than one
    attached to the Raspberry Pi's GPIO pins.
    """

    def __init__(
        self,
        gpio: Any,
        name: str,
        pin_echo: int,
        pin_trigger: int,
        burst: int,
        **kwargs: Any
    ):
        self.gpio = gpio
        self.name = name
        self.pin_echo = pin_echo
        self.pin_trigger = pin_trigger
        self.burst = burst
        self.start: Optional[float] = None
        self.distance: Optional[float] = None

        self.gpio.setup(self.pin_trigger, self.gpio.OUT)
        self.gpio.setup(self.pin_echo, self.gpio.IN)
        self.gpio.remove_event_detect(self.pin_echo)
        self.gpio.output(self.pin_trigger, False)

        # Setup-time for Sensor
        time.sleep(1)

        # create callback triggered by rising and falling edge
        def measure_callback(pin: int) -> None:
            if self.gpio.input(self.pin_echo) == 1:
                # Echo measuring begins
                self.start = time.time()
            elif self.start is not None:
                # Echo measuring completed
                delta = time.time() - self.start
                self.distance = delta * SPEED_2

        self.gpio.add_event_detect(
            self.pin_echo, self.gpio.BOTH, callback=measure_callback
        )

    def pulse(self) -> None:
        """
        Starts measurement
        """
        self.start = None
        self.distance = None
        # create trigger pulse
        self.gpio.output(self.pin_trigger, True)
        time.sleep(PULSE)
        self.gpio.output(self.pin_trigger, False)

    def measure_range(self) -> float:
        """
        Start measures and calculate average of BURST measurements
        """
        measurements: List[float] = []
        for _ in range(self.burst):
            self.pulse()
            timeout = time.time() + 1
            while self.distance is None:
                if time.time() > timeout:
                    break
                time.sleep(0.04)
            if self.distance is not None:
                measurements.append(self.distance)
            time.sleep(0.05)
        if not measurements:
            raise RuntimeError(
                "Unable to measure range on HC-SR04 sensor '%s'" % self.name
            )
        return mean(measurements)


class Sensor(GenericSensor):
    """
    Implementation of the sensor using Raspberry Pi on-board GPIO.
    """

    SENSOR_SCHEMA: CerberusSchemaType = {
        "pin_echo": {"type": "integer", "required": True, "empty": False},
        "pin_trigger": {"type": "integer", "required": True, "empty": False},
        "burst": {"type": "integer", "required": True, "empty": False},
    }

    def setup_module(self) -> None:
        # pylint: disable=import-outside-toplevel,import-error
        import RPi.GPIO as GPIO  # type: ignore

        # use BCM GPIO-references (instead of Pin-numbers)
        GPIO.setmode(GPIO.BCM)
        self.gpio = GPIO
        self.sensors: Dict[str, HCSR04] = {}

    def setup_sensor(self, sens_conf: ConfigType) -> None:
        sensor = HCSR04(gpio=self.gpio, **sens_conf)
        self.sensors[sensor.name] = sensor

    def get_value(self, sens_conf: ConfigType) -> SensorValueType:
        return self.sensors[sens_conf["name"]].measure_range()

    def cleanup(self) -> None:
        self.gpio.cleanup()
