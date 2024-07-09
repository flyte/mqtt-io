"""
Contains the base class that is shared across all Stream modules.
"""

import asyncio
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor
from typing import Optional

from ...types import ConfigType


class GenericStream(ABC):
    """
    Abstracts a generic stream interface to be implemented
    by the modules in this directory.
    """

    def __init__(self, config: ConfigType):
        self.config = config
        self.setup_module()
        self.executor = ThreadPoolExecutor()

    @abstractmethod
    def setup_module(self) -> None:
        """
        Configure the module, open ports etc.
        """

    @abstractmethod
    def read(self) -> Optional[bytes]:
        """
        Read all available bytes from the stream. Return None if no bytes were available.
        """

    @abstractmethod
    def write(self, data: bytes) -> None:
        """
        Write bytes to the stream.
        """

    async def async_read(self) -> Optional[bytes]:
        """
        Use a ThreadPoolExecutor to call the module's synchronous read method.
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, self.read)

    async def async_write(self, data: bytes) -> None:
        """
        Use a ThreadPoolExecutor to call the module's synchronous write method.
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, self.write, data)

    def cleanup(self) -> None:
        """
        Called when closing the program to handle any cleanup operations.
        """
