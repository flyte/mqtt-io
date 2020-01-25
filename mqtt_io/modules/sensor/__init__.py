import abc
import asyncio
from concurrent.futures import ThreadPoolExecutor


class GenericSensor:
    """
    Abstracts a generic sensor interface to be implemented
    by the modules in this directory.
    """

    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def setup_sensor(self):
        pass

    @abc.abstractmethod
    def get_value(self):
        pass

    def cleanup(self):
        """
        Called when closing the program to handle any cleanup operations.
        """
        pass

    async def async_get_value(self):
        """
        Use a ThreadPoolExecutor to call the module's synchronous get_value function.
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(ThreadPoolExecutor(), self.get_value)
