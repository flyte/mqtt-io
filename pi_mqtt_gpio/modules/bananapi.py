from pi_mqtt_gpio.modules import GenericGPIO, PinDirection, PinPullup


REQUIREMENTS = (
    "git+https://github.com/BPI-SINOVOIP/BPI-WiringPi2-Python.git",
)
CONFIG_SCHEMA = {
    "pin_mode": {
        "type": "string",
        "required": False,
        "default": "pins",
        "allowed": [
            "pins",
            "gpio",
            "sys"
        ]
    }
}

DIRECTIONS = None
PULLUPS = None


class GPIO(GenericGPIO):
    """
    Implementation of GPIO class for BananaPi native GPIO.
    """
    def __init__(self, config):
        global DIRECTIONS, PULLUPS
        import wiringpi2 as wpi
        self.io = wpi
        DIRECTIONS = {
            PinDirection.INPUT: wpi.GPIO.INPUT,
            PinDirection.OUTPUT: wpi.GPIO.OUTPUT
        }
        PULLUPS = {
            PinPullup.OFF: wpi.GPIO.PUD_OFF,
            PinPullup.UP: wpi.GPIO.PUD_UP,
            PinPullup.DOWN: wpi.GPIO.PUD_DOWN
        }

        pin_mode = config.get('pin_mode')
        if pin_mode == 'gpio':
            wpi.wiringPiSetupGpio()
        elif pin_mode == 'sys':
            wpi.wiringPiSetupSys()
        else:
            wpi.wiringPiSetup()

    def setup_pin(self, pin, direction, pullup, pin_config):
        self.io.pinMode(pin, DIRECTIONS[direction])
        if pullup is not None:
            self.io.pullUpDnControl(pin, PULLUPS[pullup])

    def set_pin(self, pin, value):
        self.io.digitalWrite(pin, int(value))

    def get_pin(self, pin):
        return bool(self.io.digitalRead(pin))

    def cleanup(self):
        pass
