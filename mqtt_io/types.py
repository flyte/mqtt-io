"""
Types used in MQTT IO type hints.
"""
from typing import TYPE_CHECKING, Any, Dict, Union

import trio

if TYPE_CHECKING:
    import asyncio
    from concurrent.futures import Future as ConcurrentFuture

ConfigType = Dict[str, Any]
PinType = Union[str, int]
SensorValueType = Union[float, int, None]
CerberusSchemaType = Dict[str, Any]
TaskStatus = trio._core._run._TaskStatus  # pylint: disable=protected-access
