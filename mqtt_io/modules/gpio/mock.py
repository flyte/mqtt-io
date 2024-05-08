"""
Mock GPIO module for using with the tests.
"""

from typing import Any, Callable, Dict, Iterable, List, Optional
from unittest.mock import Mock

from ...types import ConfigType, PinType
from . import GenericGPIO, InterruptEdge, InterruptSupport, PinDirection, PinPUD

REQUIREMENTS = ()
CONFIG_SCHEMA = {"test": {"type": 'boolean', "required": False, "default": False}}


# pylint: disable=useless-super-delegation,too-many-instance-attributes
class GPIO(GenericGPIO):
    """
    Mock GPIO module for using with the tests.
    """

    INTERRUPT_SUPPORT = (
        InterruptSupport.SOFTWARE_CALLBACK
        | InterruptSupport.FLAG_REGISTER
        | InterruptSupport.CAPTURE_REGISTER
    )
    PIN_SCHEMA = {
        "test": {"type": 'boolean', "required": False, "default": False},
    }

    def __init__(self, config: ConfigType):
        self.setup_module = Mock()  # type: ignore[assignment]
        self.setup_pin = Mock()  # type: ignore[assignment]
        self.setup_interrupt = Mock()  # type: ignore[assignment]
        self.setup_interrupt_callback = Mock()  # type: ignore[assignment]
        self.set_pin = Mock()  # type: ignore[assignment]
        self.get_pin = Mock(return_value=True)  # type: ignore[assignment]
        self.get_int_pins = Mock(return_value=1)  # type: ignore[assignment]
        self.get_captured_int_pin_values = Mock(return_value={1: 1})  # type: ignore[assignment]

        super().__init__(config)
        self.interrupt_callbacks: Dict[
            PinType, Callable[[List[Any], Dict[Any, Any]], None]
        ] = {}

    def setup_interrupt_callback(
        self,
        pin: PinType,
        edge: InterruptEdge,
        in_conf: ConfigType,
        callback: Callable[[List[Any], Dict[Any, Any]], None],
    ) -> None:
        self.interrupt_callbacks[pin] = callback

    def setup_module(self) -> None:
        return super().setup_module()

    def setup_pin(
        self,
        pin: PinType,
        direction: PinDirection,
        pullup: PinPUD,
        pin_config: ConfigType,
        initial: Optional[str] = None,
    ) -> None:
        return super().setup_pin(pin, direction, pullup, pin_config, initial=initial)

    def setup_interrupt(
        self, pin: PinType, edge: InterruptEdge, in_conf: ConfigType
    ) -> None:
        return super().setup_interrupt(pin, edge, in_conf)

    def set_pin(self, pin: PinType, value: bool) -> None:
        return super().set_pin(pin, value)

    def get_pin(self, pin: PinType) -> bool:
        return super().get_pin(pin)

    def get_int_pins(self) -> List[PinType]:
        return super().get_int_pins()

    def get_captured_int_pin_values(
        self, pins: Optional[Iterable[PinType]] = None
    ) -> Dict[PinType, bool]:
        return super().get_captured_int_pin_values(pins=pins)
