from __future__ import print_function

from . import GenericGPIO


class GPIO(GenericGPIO):
    """
    Implementation of GPIO class for outputting to STDIO.
    """

    def setup_module(self):
        print("setup_module()")

    def setup_pin(self, pin, direction, pullup, initial=None, **kwargs):
        print(
            "setup_pin(pin=%r, direction=%r, pullup=%r, kwargs=%r)"
            % (pin, direction, pullup, kwargs)
        )
        if initial is not None:
            if initial == "high":
                self.set_pin(pin, True)
            elif initial == "low":
                self.set_pin(pin, False)

    async def async_set_pin(self, pin, value):
        self.set_pin(pin, value)

    def set_pin(self, pin, value):
        print("set_pin(pin=%r, value=%r)" % (pin, value))

    async def async_get_pin(self, pin):
        return self.get_pin(pin)

    def get_pin(self, pin):
        print("get_pin(pin=%r)" % pin)
        return False
