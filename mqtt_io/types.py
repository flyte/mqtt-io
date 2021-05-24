"""
Types used in MQTT IO type hints.
"""
from typing import (
    # List,
    # Mapping,
    # MutableMapping,
    TYPE_CHECKING,
    Any,
    Dict,
    # Protocol,
    # Tuple,
    # Type,
    TypeVar,
    Union,
)

# import trio

if TYPE_CHECKING:
    from .events import Event  # pylint: disable=cyclic-import

T = TypeVar("T")  # pylint: disable=invalid-name
EventT = TypeVar("EventT", bound="Event")

ConfigType = Dict[str, Any]
PinType = Union[str, int]
SensorValueType = Union[float, int, None]
CerberusSchemaType = Dict[str, Any]


# class EventBusChannelDict(Protocol):
#     def __getitem__(
#         self, item: Type[EventT]
#     ) -> Tuple[trio.MemorySendChannel[EventT], trio.MemoryReceiveChannel[EventT]]:
#         ...

#     # def setdefault(
#     #     self,
#     #     __key: Type[EventT],
#     #     __default: List[
#     #         Tuple[trio.MemorySendChannel[EventT], trio.MemoryReceiveChannel[EventT]]
#     #     ],
#     # ) -> List[Tuple[trio.MemorySendChannel[EventT], trio.MemoryReceiveChannel[EventT]]]:
#     #     ...

#     def setdefault(self, key: _KT, default: _VT = ...) -> _VT:
#         ...
