from os.path import exists

from . import GenericGPIO


class GPIO(GenericGPIO):
    """
    Implementation of GPIO class for checking if a file path exists.
    """

    def __init__(self, config):
        pass

    def setup_pin(self, pin, direction, pullup, pin_config):
        pass

    def set_pin(self, pin, value):
        pass

    async def async_get_pin(self, pin):
        return self.get_pin(pin)

    def get_pin(self, pin):
        return exists("/tmp/exists")
