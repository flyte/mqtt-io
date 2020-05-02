from pi_mqtt_gpio.modules import GenericGPIO, PinDirection, PinPullup


REQUIREMENTS = ("pySUNXI",)

DIRECTIONS = None
PULLUPS = None


class GPIO(GenericGPIO):
    """
    Implementation of GPIO class for Sunxi native GPIO.
    """

    def __init__(self, config):
        global DIRECTIONS, PULLUPS
        from pySUNXI import gpio

        self.io = gpio
        DIRECTIONS = {PinDirection.INPUT: gpio.INPUT, PinDirection.OUTPUT: gpio.OUTPUT}

        PULLUPS = {
            PinPullup.OFF: gpio.PULLNONE,
            PinPullup.UP: gpio.PULLUP,
            PinPullup.DOWN: gpio.PULLDOWN,
        }
        gpio.init()

    def setup_pin(self, pin, direction, pullup, pin_config):
        direction = DIRECTIONS[direction]

        if pullup is None:
            pullup = PULLUPS[PinPullup.OFF]
        else:
            pullup = PULLUPS[pullup]

        initial = {None: -1, "low": 0, "high": 1}[pin_config.get("initial")]
        #self.io.setup(pin, direction, pull_up_down=pullup, initial=initial)
        self.io.setcfg(pin, direction)
        self.io.pullup(pin, pullup)
        if direction==self.io.OUTPUT:
            self.io.output(pin, initial)

    def set_pin(self, pin, value):
        self.io.output(pin, value)

    def get_pin(self, pin):
        return self.io.input(pin)

    def cleanup(self):
        pass
