"""
Mock GPIO module for using with the tests.
"""

from typing import Any, Callable, Dict, List
from unittest.mock import Mock

from ....types import ConfigType, PinType
from .. import GenericGPIO, InterruptEdge, InterruptSupport

REQUIREMENTS = ()
CONFIG_SCHEMA = dict(test=dict(type="boolean", required=False, default=False))


class GPIO(GenericGPIO):
    """
    Mock GPIO module for using with the tests.
    """

    INTERRUPT_SUPPORT = (
        InterruptSupport.SOFTWARE_CALLBACK
        | InterruptSupport.FLAG_REGISTER
        | InterruptSupport.CAPTURE_REGISTER
    )

    def __init__(self, config: ConfigType):
        super().__init__(config)
        self.interrupt_callbacks: Dict[
            PinType, Callable[[List[Any], Dict[Any, Any]], None]
        ] = {}

    setup_module = Mock()
    setup_pin = Mock()

    def setup_interrupt_callback(
        self,
        pin: PinType,
        edge: InterruptEdge,
        in_conf: ConfigType,
        callback: Callable[[List[Any], Dict[Any, Any]], None],
    ) -> None:
        self.interrupt_edges[pin] = edge
        self.interrupt_callbacks[pin] = callback

    setup_interrupt = Mock()
    set_pin = Mock()
    get_pin = Mock(return_value=1)
    get_int_pins = Mock(return_value=1)
    get_captured_int_pin_values = Mock(return_value={1: 1})
