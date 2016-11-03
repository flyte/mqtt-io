from pi_mqtt_gpio.modules import GenericGPIO, PinDirection, PinPullup


REQUIREMENTS = ("RPi.GPIO",)

DIRECTIONS = None
PULLUPS = None


class GPIO(GenericGPIO):
    """
    Implementation of GPIO class for Raspberry Pi native GPIO.
    """
    def __init__(self, config):
        global DIRECTIONS, PULLUPS
        import RPi.GPIO as gpio
        self.io = gpio
        DIRECTIONS = {
            PinDirection.INPUT: gpio.IN,
            PinDirection.OUTPUT: gpio.OUT
        }

        PULLUPS = {
            PinPullup.UP: gpio.PUD_UP,
            PinPullup.DOWN: gpio.PUD_DOWN
        }

        gpio.setmode(gpio.BCM)

    def setup_pin(self, pin, direction, pullup, pin_config):
        direction = DIRECTIONS[direction]
        if pullup is not None:
            pullup = PULLUPS[pullup]
        self.io.setup(pin, direction, pull_up_down=pullup)

    def set_pin(self, pin, value):
        self.io.output(pin, value)

    def get_pin(self, pin):
        return self.io.input(pin)
