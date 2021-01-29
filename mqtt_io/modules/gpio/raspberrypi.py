from functools import partial

from . import GenericGPIO, InterruptEdge, InterruptSupport, PinDirection, PinPUD

REQUIREMENTS = ("RPi.GPIO",)

DIRECTIONS = None
PULLUPS = None
INTERRUPT = None


class GPIO(GenericGPIO):
    """
    Implementation of GPIO class for Raspberry Pi native GPIO.
    """

    INTERRUPT_SUPPORT = InterruptSupport.SOFTWARE_CALLBACK

    def setup_module(self):
        global DIRECTIONS, PULLUPS, INTERRUPT
        import RPi.GPIO as gpio

        self.io = gpio
        DIRECTIONS = {PinDirection.INPUT: gpio.IN, PinDirection.OUTPUT: gpio.OUT}

        PULLUPS = {
            PinPUD.OFF: gpio.PUD_OFF,
            PinPUD.UP: gpio.PUD_UP,
            PinPUD.DOWN: gpio.PUD_DOWN,
        }

        INTERRUPT = {
            InterruptEdge.RISING: gpio.RISING,
            InterruptEdge.FALLING: gpio.FALLING,
            InterruptEdge.BOTH: gpio.BOTH,
        }

        gpio.setmode(gpio.BCM)

    def setup_pin(self, pin, direction, pullup=None, initial=None, **kwargs):
        direction = DIRECTIONS[direction]

        if pullup is None:
            pullup = PULLUPS[PinPUD.OFF]
        else:
            pullup = PULLUPS[pullup]

        initial = {None: -1, "low": 0, "high": 1}[initial]
        self.io.setup(pin, direction, pull_up_down=pullup, initial=initial)

    def setup_interrupt(self, pin, edge, callback, in_conf):
        edge = INTERRUPT[edge]
        self.io.add_event_detect(
            pin,
            edge,
            callback=callback,
            bouncetime=in_conf.get("bouncetime", 100),
        )
        self.interrupt_edges[pin] = edge

    def get_interrupt_value(self, pin, *args, **kwargs):
        edge = self.interrupt_edges[pin]
        if edge == InterruptEdge.BOTH:
            # Polling the pin for its value is a bit crap, but I can't find any alternative
            value = self.get_pin(pin)
        else:
            # If we're listening for RISING or FALLING then we infer the pin's value
            value = edge == InterruptEdge.RISING
        return value

    def set_pin(self, pin, value):
        self.io.output(pin, value)

    def get_pin(self, pin):
        return self.io.input(pin)

    def cleanup(self):
        self.io.cleanup()
