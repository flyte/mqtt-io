"""
Contains the base class that is shared across all Stream modules.
"""

from abc import ABC, abstractmethod
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

    def cleanup(self) -> None:
        """
        Called when closing the program to handle any cleanup operations.
        """
