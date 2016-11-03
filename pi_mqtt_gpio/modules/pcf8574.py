from __future__ import absolute_import

from pi_mqtt_gpio.modules import GenericGPIO, PinDirection, PinPullup


REQUIREMENTS = ("pcf8574",)

PULLUPS = None


class GPIO(GenericGPIO):
    """
    Implementation of GPIO class for the PCF8574 IO expander chip.
    """
    def __init__(self, config):
        global PULLUPS
        PULLUPS = {
            PinPullup.UP: True,
            PinPullup.DOWN: False
        }
        i2c_bus_num = config.get("i2c_bus_num", 1)
        chip_addr = config.get("chip_addr", 0x20)
        from pcf8574 import PCF8574
        self.io = PCF8574(i2c_bus_num, chip_addr)

    def setup_pin(self, pin, direction, pullup, pin_config):
        if direction == PinDirection.INPUT and pullup is not None:
            self.io.port[pin] = PULLUPS[pullup]

    def set_pin(self, pin, value):
        self.io.port[pin] = value

    def get_pin(self, pin):
        return self.io.port[pin]
