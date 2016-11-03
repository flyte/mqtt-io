import abc

from enum import Enum


class PinDirection(Enum):
    INPUT = 0
    OUTPUT = 1


class PinPullup(Enum):
    UP = 0
    DOWN = 1


class GenericGPIO(object):
    """
    Abstracts a generic GPIO interface to be implemented by the modules in this directory.
    """
    __metaclass__ = abc.ABCMeta

    # def __init__(self, config):
    #     self.setup_gpio(config)

    #     for pin_config in config.get("digital_inputs"):
    #         pullup = None
    #         if pin_config.get("pullup"):
    #             pullup = PinPullup.UP
    #         elif pin_config.get("pulldown"):
    #             pullup = PinPullup.DOWN

    #         self.setup_pin(pin_config["pin"], PinDirection.INPUT, pullup, pin_config)

    #     for pin_config in config.get("digital_outputs"):
    #         self.setup_pin(pin_config["pin"], PinDirection.OUTPUT, None, pin_config)

    @abc.abstractmethod
    def setup_pin(self, pin, direction, pullup, pin_config):
        pass

    @abc.abstractmethod
    def set_pin(self, pin, value):
        pass

    @abc.abstractmethod
    def get_pin(self, pin):
        pass
