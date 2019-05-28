import abc

from enum import Enum


BASE_SCHEMA = {
    "name": {"required": True, "empty": False},
    "module": {"required": True, "empty": False},
    "cleanup": {"required": False, "type": "boolean", "default": True},
}


class PinDirection(Enum):
    INPUT = 0
    OUTPUT = 1


class PinPullup(Enum):
    OFF = 0
    UP = 1
    DOWN = 2


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

    def cleanup(self):
        """
        Called when closing the program to handle any cleanup operations.
        """
        pass


class GenericSensor(object):
    """
    Abstracts a generic sensor interface to be implemented
    by the modules in this directory.
    """

    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def setup_sensor(self, config):
        pass

    @abc.abstractmethod
    def get_value(self, config):
        pass

    def cleanup(self):
        """
        Called when closing the program to handle any cleanup operations.
        """
        pass
