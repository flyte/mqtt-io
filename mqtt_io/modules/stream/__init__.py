"""
Contains the base class that is shared across all Stream modules.
"""

import asyncio
import logging
import threading
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor
from typing import Optional

from ...types import ConfigType

_LOG = logging.getLogger(__name__)


class GenericStream(ABC):
    """
    Abstracts a generic stream interface to be implemented
    by the modules in this directory.
    """

    def __init__(self, config: ConfigType):
        self.config = config
        self.executor = ThreadPoolExecutor()
        self._io_lock = threading.Lock()
        try:
            self.setup_module()
        except Exception:  # pylint: disable=broad-except
            _LOG.exception("Stream setup failed; it will be retried")

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

    def reconnect(self) -> None:
        """
        Close the current handle and open the device again.

        A missing device must not block setup of other streams. The poller
        calls this after a failed read or write.
        """
        with self._io_lock:
            try:
                self.cleanup()
            except Exception:  # pylint: disable=broad-except
                _LOG.exception("Stream cleanup before reopen failed")
            self.setup_module()

    def _read_locked(self) -> Optional[bytes]:
        with self._io_lock:
            return self.read()

    def _write_locked(self, data: bytes) -> None:
        with self._io_lock:
            self.write(data)

    async def async_read(self) -> Optional[bytes]:
        """
        Use a ThreadPoolExecutor to call the module's synchronous read method.
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, self._read_locked)

    async def async_write(self, data: bytes) -> None:
        """
        Use a ThreadPoolExecutor to call the module's synchronous write method.
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, self._write_locked, data)

    async def async_reconnect(self) -> None:
        """Reopen the device without blocking the event loop."""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(self.executor, self.reconnect)

    def cleanup(self) -> None:
        """
        Called when closing the program to handle any cleanup operations.
        """
