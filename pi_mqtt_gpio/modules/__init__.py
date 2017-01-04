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
    Abstracts a generic GPIO interface to be implemented by the modules in this
    directory.
    """
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def setup_pin(self, pin, direction, pullup, pin_config):
        pass

    @abc.abstractmethod
    def set_pin(self, pin, value):
        pass

    @abc.abstractmethod
    def get_pin(self, pin):
        pass
