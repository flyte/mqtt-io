"""
Contains the base class that is shared across all Sensor modules.
"""

import abc
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from ...types import ConfigType, SensorValueType


class GenericSensor(abc.ABC):
    """
    Abstracts a generic sensor interface to be implemented
    by the modules in this directory.
    """

    def __init__(self, config: ConfigType):
        self.config = config
        self.sensor: Any = None
        self.setup_module()
        self.executor = ThreadPoolExecutor()

    @abc.abstractmethod
    def get_value(self, sens_conf: ConfigType) -> SensorValueType:
        """
        Read the sensor's current value.
        """

    def setup_module(self) -> None:
        """
        Called on initialisation of the Sensor module during the startup phase.

        The module's config from the `sensor_modules` section of the config file is stored
        in `self.config`.
        """

    def setup_sensor(self, sens_conf: ConfigType) -> None:
        """
        Called on initialisation of each reading type of the Sensor module during the
        startup phase.

        The `sens_conf` passed in here is the sensor's entry in the `sensor_inputs`
        section of the config file.
        """

    def cleanup(self) -> None:
        """
        Called when closing the program to handle any cleanup operations.
        """

    async def async_get_value(self, sens_conf: ConfigType) -> SensorValueType:
        """
        Use a ThreadPoolExecutor to call the module's synchronous get_value function.
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, self.get_value, sens_conf)
