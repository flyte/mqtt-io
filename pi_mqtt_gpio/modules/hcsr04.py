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
        self.pin_Trigger = config["pin_trigger"]
        self.pin_Echo = config["pin_echo"]
        self.burst = config["burst"]

    def setup_sensor(self, config):
        # use BCM GPIO-references (instead of Pin-numbers)
        # and define GPIO-input/output
        self.gpio.setmode(self.gpio.BCM)
        self.gpio.setup(self.pin_Trigger,self.gpio.OUT)
        self.gpio.setup(self.pin_Echo,self.gpio.IN)
        self.gpio.remove_event_detect(self.pin_Echo)
        self.gpio.output(self.pin_Trigger, False)
        time.sleep(1)                           # Setup-time for Sensor
        self.gpio.add_event_detect(self.pin_Echo, self.gpio.BOTH, callback=self.measure)    # create callback triggered by rising and falling edge

        self.stopp = 0
        self.start = 0
        self.distance = 0

        return True

    def get_value(self, config):
        value = self.measure_range()
        return value

    def pulse(self):                            # function to start measurement
      self.gpio.output(self.pin_Trigger, True)  # create trigger pulse
      time.sleep(PULSE)
      self.gpio.output(self.pin_Trigger, False)
      self.stopp = 0
      self.start = 0
      self.distance = 0

    def measure(self, x):                       # Callback-Function for echo signal
      if self.gpio.input(self.pin_Echo) == 1:   # save time of rising echo signal
        self.start = time.time()
      else:                                     # falling edge, save time
        self.stopp = time.time()
        delta = self.stopp - self.start         # calculate time difference sending / receiving
        self.distance = delta * SPEED_2         # calculate distance by time and sonic speed

    def measure_range(self):                    # start measures and calculate average of BURST measurements
      values = []
      sum = 0
      for i in range(0, self.burst):
        self.pulse()                            # start measurement
        time.sleep(0.040)                       # wait till end of measurement
        values.append(self.distance)            # save value in array and sum up
        sum = sum + values[i]
        time.sleep(0.05)
      return sum/self.burst;                         # return average

    def cleanup(self):
        self.gpio.cleanup()
