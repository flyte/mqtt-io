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
        pass

    @abstractmethod
    def read(self) -> Optional[bytes]:
        pass

    @abstractmethod
    def write(self, data: bytes) -> None:
        pass

    def cleanup(self) -> None:
        """
        Called when closing the program to handle any cleanup operations.
        """
        pass
