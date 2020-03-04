from pi_mqtt_gpio.modules import GenericSensor
import time
import datetime

REQUIREMENTS = ("RPi.GPIO",)

# HC-SR04 ultrasonic sensor_inputs
# for use at Raspberry Pi, the ECHO signal of the sensor must be reduced to 3.3V, since the sensor works with 5V!!
# You can simply reduce with a 3.9kOhm and 6.8kOhm resistor voltage reduction
#
# further information at http://www.netzmafia.de/skripten/hardware/RasPi/Projekt-Ultraschall/
# The code is based on the sample code of this webpage by Prof.Plate / University of Munich

CONFIG_SCHEMA = {
    "pin_echo": {"type": "integer", "required": True, "empty": False},
    "pin_trigger": {"type": "integer", "required": True, "empty": False},
    "burst": {"type": "integer", "required": True, "empty": False},
}
# duration trigger pulse
PULSE = 0.00001
# sonic speed/2
SPEED_2 = 17015


class Sensor(GenericSensor):
    def __init__(self, config):
        import RPi.GPIO as GPIO

        self.gpio = GPIO
        self.pin_trigger = config["pin_trigger"]
        self.pin_echo = config["pin_echo"]
        self.burst = config["burst"]

    def setup_sensor(self, config):
        # use BCM GPIO-references (instead of Pin-numbers)
        # and define GPIO-input/output
        self.gpio.setmode(self.gpio.BCM)
        self.gpio.setup(self.pin_trigger, self.gpio.OUT)
        self.gpio.setup(self.pin_echo, self.gpio.IN)
        self.gpio.remove_event_detect(self.pin_echo)
        self.gpio.output(self.pin_trigger, False)
        # Setup-time for Sensor
        time.sleep(1)
        # create callback triggered by rising and falling edge
        self.gpio.add_event_detect(self.pin_echo, self.gpio.BOTH, callback=self.measure)

        self.stop = 0
        self.start = 0
        self.distance = 0

        return True

    def get_value(self, config):
        value = self.measure_range()
        return value

    def pulse(self):
        """
        Starts measurement
        """
        # create trigger pulse
        self.gpio.output(self.pin_trigger, True)
        time.sleep(PULSE)
        self.gpio.output(self.pin_trigger, False)
        self.stop = 0
        self.start = 0
        self.distance = 0

    def measure(self, x):
        """
        Callback function for echo signal
        """
        if self.gpio.input(self.pin_echo) == 1:
            # save time of rising echo signal
            self.start = time.time()
        else:
            # falling edge, save time
            self.stop = time.time()
            # calculate time difference sending / receiving
            delta = self.stop - self.start
            # calculate distance by time and sonic speed
            self.distance = delta * SPEED_2

    def measure_range(self):
        """
        Start measures and calculate average of BURST measurements
        """
        values = []
        ranges_sum = 0
        for i in range(0, self.burst):
            # start measurement
            self.pulse()
            # wait till end of measurement
            time.sleep(0.040)
            # save value in array and sum up
            values.append(self.distance)
            ranges_sum += values[i]
            time.sleep(0.05)
        # return average
        return ranges_sum / self.burst

    def cleanup(self):
        self.gpio.cleanup()
