from __future__ import absolute_import

from . import GenericGPIO, PinDirection, PinPUD


REQUIREMENTS = ("pcf8574",)
CONFIG_SCHEMA = {
    "i2c_bus_num": {"type": "integer", "required": True, "empty": False},
    "chip_addr": {"type": "integer", "required": True, "empty": False},
}

PULLUPS = None


class GPIO(GenericGPIO):
    """
    Implementation of GPIO class for the PCF8574 IO expander chip.
    """

    def __init__(self, config):
        global PULLUPS
        PULLUPS = {PinPUD.UP: True, PinPUD.DOWN: False}
        from pcf8574 import PCF8574

        self.io = PCF8574(config["i2c_bus_num"], config["chip_addr"])

    def setup_pin(self, pin, direction, pullup, pin_config):
        if direction == PinDirection.INPUT and pullup is not None:
            self.io.port[pin] = PULLUPS[pullup]
        # FIXME: Needing refactor or cleanup -@flyte at 26/01/2020, 15:48:43
        # Modules shouldn't know about config. We should have a specific API
        # for setup_pin etc. including 'initial', or using kwargs if necessary.
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
