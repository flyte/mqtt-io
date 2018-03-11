from pi_mqtt_gpio.modules import GenericGPIO, PinDirection, PinPullup


REQUIREMENTS = ("OPi.GPIO",)

DIRECTIONS = None
PULLUPS = None


class GPIO(GenericGPIO):
    """
    Implementation of GPIO class for Raspberry Pi native GPIO.
    """
    def __init__(self, config):
        global DIRECTIONS, PULLUPS
        import OPi.GPIO as gpio
        self.io = gpio
        DIRECTIONS = {
            PinDirection.INPUT: gpio.IN,
            PinDirection.OUTPUT: gpio.OUT
        }

        PULLUPS = {
            PinPullup.OFF: 0,
            PinPullup.UP: 0,
            PinPullup.DOWN: 0, #gpio.PUD_DOWN
        }

        gpio.setmode(gpio.BOARD)

    def setup_pin(self, pin, direction, pullup, pin_config):
        direction = DIRECTIONS[direction]

        if pullup is None:
            pullup = PULLUPS[PinPullup.OFF]
        else:
            pullup = PULLUPS[pullup]

        initial = {
            None: -1,
            "low": 0,
            "high": 1
        }[pin_config.get("initial")]
        self.io.setup(pin, direction, pull_up_down=pullup, initial=initial)

    def set_pin(self, pin, value):
        self.io.output(pin, value)

    def get_pin(self, pin):
        return self.io.input(pin)

    def cleanup(self):
        self.io.cleanup()
