from pi_mqtt_gpio.modules import GenericGPIO, PinDirection, PinPullup, \
                                 InterruptEdge

REQUIREMENTS = ("RPi.GPIO",)

DIRECTIONS = None
PULLUPS = None
INTERRUPT = None
GPIO_INTERRUPT_CALLBACK_LOOKUP = {}


class GPIO(GenericGPIO):
    """
    Implementation of GPIO class for Raspberry Pi native GPIO.
    """

    def __init__(self, config):
        global DIRECTIONS, PULLUPS, INTERRUPT
        import RPi.GPIO as gpio

        self.io = gpio
        DIRECTIONS = {PinDirection.INPUT: gpio.IN, PinDirection.OUTPUT: gpio.OUT}

        PULLUPS = {
            PinPullup.OFF: gpio.PUD_OFF,
            PinPullup.UP: gpio.PUD_UP,
            PinPullup.DOWN: gpio.PUD_DOWN,
        }

        INTERRUPT = {
            InterruptEdge.RISING: gpio.RISING,
            InterruptEdge.FALLING: gpio.FALLING,
            InterruptEdge.BOTH: gpio.BOTH
        }

        gpio.setmode(gpio.BCM)

    def setup_pin(self, pin, direction, pullup, pin_config):
        direction = DIRECTIONS[direction]

        if pullup is None:
            pullup = PULLUPS[PinPullup.OFF]
        else:
            pullup = PULLUPS[pullup]

        initial = {None: -1, "low": 0, "high": 1}[pin_config.get("initial")]
        self.io.setup(pin, direction, pull_up_down=pullup, initial=initial)

    def setup_interrupt(self, handle, pin, edge, callback, bouncetime=100):
        """
        install interrupt callback function
        handle:     is returned in the callback function as identification
        pin:        gpio to watch for interrupts
        edge:       triggering edge: RISING, FALLING or BOTH
        callback:   the callback function to be called, when interrupt occurs
        bouncetime: minimum time between two interrupts
        """
        edge = INTERRUPT[edge]
        self.io.add_event_detect(pin, edge, callback=self.interrupt_callback,
                                 bouncetime=bouncetime)
        self.GPIO_INTERRUPT_CALLBACK_LOOKUP[pin] = {"handle": handle,
                                                    "callback": callback}

    def set_pin(self, pin, value):
        self.io.output(pin, value)

    def get_pin(self, pin):
        return self.io.input(pin)

    def cleanup(self):
        self.io.cleanup()
