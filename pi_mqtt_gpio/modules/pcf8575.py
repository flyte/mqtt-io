from __future__ import absolute_import

from pi_mqtt_gpio.modules import GenericGPIO, PinDirection, PinPullup


REQUIREMENTS = ("pcf8575",)
CONFIG_SCHEMA = {
    "i2c_bus_num": {"type": "integer", "required": True, "empty": False},
    "chip_addr": {"type": "integer", "required": True, "empty": False},
}

PULLUPS = None


class GPIO(GenericGPIO):
    """
    Implementation of GPIO class for the pcf8575 IO expander chip.
    """

    def __init__(self, config):
        global PULLUPS
        PULLUPS = {PinPullup.UP: True, PinPullup.DOWN: False}
        from pcf8575 import pcf8575

        self.io = pcf8575(config["i2c_bus_num"], config["chip_addr"])

    def setup_pin(self, pin, direction, pullup, pin_config):
        if direction == PinDirection.INPUT and pullup is not None:
            self.io.port[pin] = PULLUPS[pullup]
        initial = pin_config.get("initial")
        if initial is not None:
            if initial == "high":
                self.set_pin(pin, True)
            elif initial == "low":
                self.set_pin(pin, False)

    def set_pin(self, pin, value):
        self.io.port[pin] = value

    def get_pin(self, pin):
        return self.io.port[pin]
