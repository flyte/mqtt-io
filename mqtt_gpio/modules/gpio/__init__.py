import abc
import asyncio
from concurrent.futures import ThreadPoolExecutor
from enum import Enum


class PinDirection(Enum):
    INPUT = 0
    OUTPUT = 1


class PinPUD(Enum):
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

    async def async_set_pin(self, pin, value):
        """
        Use a ThreadPoolExecutor to call the module's synchronous set_pin function.
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(ThreadPoolExecutor(), self.set_pin, pin, value)

    async def async_get_pin(self, pin, value):
        """
        Use a ThreadPoolExecutor to call the module's synchronous get_pin function.
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(ThreadPoolExecutor(), self.get_pin, pin)
