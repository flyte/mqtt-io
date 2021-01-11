from pi_mqtt_gpio.modules import GenericGPIO, PinDirection, PinPullup, \
                                 InterruptEdge

import threading
import queue
from datetime import datetime, timedelta

# Requires libgpiod-devel, libgpiod
REQUIREMENTS = ("gpiod",)

CONFIG_SCHEMA = {
    "chip": {
        "type": "string",
        "required": False,
        "default": "/dev/gpiochip0"
    }
}

DIRECTIONS = None
PULLUPS = None
INTERRUPT = None
GPIO_INTERRUPT_CALLBACK_LOOKUP = {}

class GPIO(GenericGPIO):
    """
    Implementation of GPIO class for libgpiod (linux kernel >= 4.8).
    """

    def __init__(self, config):
        global DIRECTIONS, PULLUPS, INTERRUPT
        import gpiod as gpio

        self.io = gpio
        self.chip = gpio.chip(config["chip"])
        self.pins = {}
        self.watchers = {}

        DIRECTIONS = {PinDirection.INPUT: gpio.line_request.DIRECTION_INPUT, PinDirection.OUTPUT: gpio.line_request.DIRECTION_OUTPUT}

        INTERRUPT = {
            InterruptEdge.RISING: gpio.line_request.EVENT_RISING_EDGE,
            InterruptEdge.FALLING: gpio.line_request.EVENT_FALLING_EDGE,
            InterruptEdge.BOTH: gpio.line_request.EVENT_BOTH_EDGES
        }

    def setup_pin(self, pin, direction, pullup, pin_config):
        """
        setup a pin as either input or output.
        pin:        offset to use the gpio line
        direction:  input or output
        pullup:     pullup settings are not supported
        """
        line_direction = DIRECTIONS[direction]
        offset = pin

        # Pullup settings are called bias in libgpiod and are only
        # available since Linux Kernel 5.5. They are as of now not 
        # yet part of python3-gpiod.

        pin = self.chip.get_line(offset)

        config = self.io.line_request()
        config.consumer = 'pi-mqtt-gpio'
        config.request_type = line_direction

        pin.request(config)
        self.pins[offset] = pin

    def set_pin(self, pin, value):
        offset = pin
        self.pins[offset].set_value(value)

    def get_pin(self, pin):
        offset = pin
        return self.pins[offset].get_value()

    def cleanup(self):
        pass
