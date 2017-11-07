from pi_mqtt_gpio.modules import GenericGPIO, PinDirection, PinPullup


REQUIREMENTS = ("RPi.GPIO>=0.5.2a",)

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
            PinPullup.OFF: gpio.PUD_OFF,
            PinPullup.UP: gpio.PUD_UP,
            PinPullup.DOWN: gpio.PUD_DOWN
        }

        gpio.setmode(gpio.BCM)
        self.pwms = {}

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

    def setup_pwm(self, pin, freq, duty=50):
        self.io.setup(pin, self.io.OUT)
        pwm_config = dict(
            freq=freq,
            duty=duty,
            obj=self.io.PWM(pin, freq)
        )
        pwm_config["obj"].ChangeDutyCycle(duty)
        self.pwms[pin] = pwm_config

    def start_pwm(self, pin):
        # @TODO: KeyError
        self.pwms[pin]["obj"].start(self.pwms[pin]["duty"])

    def stop_pwm(self, pin):
        # @TODO: KeyError
        self.pwms[pin]["obj"].stop()

    def set_pwm_frequency(self, pin, freq):
        # @TODO: KeyError
        self.pwms[pin]["obj"].ChangeFrequency(freq)
        self.pwms[pin]["freq"] = freq

    def set_pwm_duty(self, pin, duty):
        # @TODO: KeyError
        self.pwms[pin]["obj"].ChangeDutyCycle(duty)
        self.pwms[pin]["duty"] = duty
