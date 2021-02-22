"""
Utility functions for the tests.
"""

import asyncio
from typing import Any

import yaml

from ..config import validate_and_normalise_main_config
from ..types import ConfigType


def validate_config(yaml_config: str) -> ConfigType:
    """
    Load and validate the provided config.
    """
    return validate_and_normalise_main_config(yaml.safe_load(yaml_config))


def get_coro(task: "asyncio.Task[Any]") -> Any:
    """
    Get a task's coroutine.
    """
    # pylint: disable=protected-access
    if hasattr(task, "get_coro"):
        return task.get_coro()  # type: ignore[attr-defined]
    if hasattr(task, "_coro"):
        return task._coro  # type: ignore[attr-defined]
    raise AttributeError("Unable to get task's coro")
