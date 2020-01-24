import abc

from enum import Enum
from time import sleep


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


class InterruptEdge(Enum):
    RISING = 0
    FALLING = 1
    BOTH = 2


class GenericGPIO(object):
    """
    Abstracts a generic GPIO interface to be implemented by the modules in this
    directory.
    """

    __metaclass__ = abc.ABCMeta
    GPIO_INTERRUPT_CALLBACK_LOOKUP = {}

    @abc.abstractmethod
    def setup_pin(self, pin, direction, pullup, pin_config):
        pass

    # may be overloaded, if module supports interrupts
    def setup_interrupt(self, handle, pin, edge, callback, bouncetime):
        raise(NotImplementedError)

    @abc.abstractmethod
    def set_pin(self, pin, value):
        pass

    @abc.abstractmethod
    def get_pin(self, pin):
        pass

    def interrupt_callback(self, pin):
        """
        This function should not be overloaded, but be registered in the ISR
        of the module triggering the interrupt
        """
        callback = self.GPIO_INTERRUPT_CALLBACK_LOOKUP[pin].get("callback")
        handle = self.GPIO_INTERRUPT_CALLBACK_LOOKUP[pin].get("handle")
        callback(handle, pin)

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
