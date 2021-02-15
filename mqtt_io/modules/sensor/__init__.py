import abc
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from ...types import ConfigType, SensorValueType


class GenericSensor:
    """
    Abstracts a generic sensor interface to be implemented
    by the modules in this directory.
    """

    __metaclass__ = abc.ABCMeta

    def __init__(self, config: ConfigType):
        self.config = config
        self.sensor: Any = None
        self.setup_sensor(config)

    @abc.abstractmethod
    def get_value(self, sens_conf: ConfigType) -> SensorValueType:
        pass

    def setup_sensor(self, config: ConfigType) -> None:
        pass

    def cleanup(self) -> None:
        """
        Called when closing the program to handle any cleanup operations.
        """
        pass

    async def async_get_value(self, sens_conf: ConfigType) -> SensorValueType:
        """
        Use a ThreadPoolExecutor to call the module's synchronous get_value function.
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(ThreadPoolExecutor(), self.get_value, sens_conf)
