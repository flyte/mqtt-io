from pi_mqtt_gpio.modules import GenericGPIO, PinDirection, PinPullup, InterruptEdge

import threading
import queue
from datetime import datetime, timedelta

# Requires libgpiod-devel, libgpiod
REQUIREMENTS = ("gpiod",)

CONFIG_SCHEMA = {
    "chip": {"type": "string", "required": False, "default": "/dev/gpiochip0"}
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

        DIRECTIONS = {
            PinDirection.INPUT: gpio.line_request.DIRECTION_INPUT,
            PinDirection.OUTPUT: gpio.line_request.DIRECTION_OUTPUT,
        }

        INTERRUPT = {
            InterruptEdge.RISING: gpio.line_request.EVENT_RISING_EDGE,
            InterruptEdge.FALLING: gpio.line_request.EVENT_FALLING_EDGE,
            InterruptEdge.BOTH: gpio.line_request.EVENT_BOTH_EDGES,
        }

    def setup_pin(self, pin, direction, pullup, pin_config):
        """
        setup a pin as either input or output.
        pin:        offset to use the gpio line
        direction:  input or output
        pullup:     pullup settings are not supported
        """
        # Pullup settings are called bias in libgpiod and are only
        # available since Linux Kernel 5.5. They are as of now not
        # yet part of python3-gpiod.

        line = self.chip.get_line(pin)

        config = self.io.line_request()
        config.consumer = "pi-mqtt-gpio"
        config.request_type = DIRECTIONS[direction]

        line.request(config)
        self.pins[pin] = line

    def setup_interrupt(self, handle, pin, edge, callback, bouncetime=100):
        """
        install interrupt callback function
        handle:     is returned in the callback function as identification
        pin:        gpio to watch for interrupts
        edge:       triggering edge: RISING, FALLING or BOTH
        callback:   the callback function to be called, when interrupt occurs
        bouncetime: minimum time between two interrupts
        """

        config = self.io.line_request()
        config.consumer = "pi-mqtt-gpio"
        config.request_type = INTERRUPT[edge]

        t = GpioThread(
            chip=self.chip,
            offset=pin,
            config=config,
            callback=self.interrupt_callback,
            bouncetime=bouncetime,
        )
        t.start()

        self.GPIO_INTERRUPT_CALLBACK_LOOKUP[pin] = {
            "handle": handle,
            "callback": callback,
        }

    def set_pin(self, pin, value):
        offset = pin
        self.pins[offset].set_value(value)

    def get_pin(self, pin):
        offset = pin
        return self.pins[offset].get_value()

    def cleanup(self):
        pass


class GpioThread(threading.Thread):
    def __init__(self, chip, offset, config, callback, bouncetime):
        super().__init__()
        self.daemon = True

        self.offset = offset
        self.pin = chip.get_line(self.offset)
        self.pin.release()
        self.pin.request(config)
        self.callback = callback
        self.bouncetime = timedelta(microseconds=bouncetime)

    def run(self):
        previous_event_time = datetime.now()
        while True:
            if self.pin.event_wait(timedelta(seconds=10)):
                event = self.pin.event_read()
                event.timestamp = datetime.now()
                if event.timestamp - previous_event_time > self.bouncetime:
                    previous_event_time = event.timestamp
                    self.callback(self.offset)
