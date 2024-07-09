"""
GPIO Zero
"""
import logging
from functools import partial
from typing import Optional, Any, Callable, List, Dict, TYPE_CHECKING, cast

from mqtt_io.modules.gpio import (
    GenericGPIO,
    PinDirection,
    PinPUD,
    InterruptSupport,
    InterruptEdge,
)
from mqtt_io.types import PinType, ConfigType

if TYPE_CHECKING:
    # pylint: disable=import-error
    import gpiozero  # type: ignore

_LOG = logging.getLogger(__name__)
REQUIREMENTS = ("gpiozero",)


class GPIO(GenericGPIO):
    """
    Implementation of GPIO class for gpiozero
    """

    INTERRUPT_SUPPORT = InterruptSupport.SOFTWARE_CALLBACK
    PIN_SCHEMA = {
        "kwargs": {
            "type": "dict",
            "required": False,
            "default": {},
        }
    }
    INPUT_SCHEMA = {"class": {"type": "string", "required": False, "default": "Button"}}
    OUTPUT_SCHEMA = {"class": {"type": "string", "required": False, "default": "LED"}}

    def setup_module(self) -> None:
        # pylint: disable=import-outside-toplevel,import-error
        import gpiozero

        self.io = gpiozero
        self._in_pins: Dict[PinType, gpiozero.InputDevice] = {}
        self._out_pins: Dict[PinType, gpiozero.OutputDevice] = {}
        self.pullup_map = {
            PinPUD.OFF: None,
            PinPUD.UP: True,
            PinPUD.DOWN: False,
        }

    def setup_pin(
        self,
        pin: PinType,
        direction: PinDirection,
        pullup: PinPUD,
        pin_config: ConfigType,
        initial: Optional[str] = None,
    ) -> None:

        if direction == PinDirection.OUTPUT:
            pin_config.setdefault("initial_value", initial)
            cls = getattr(self.io, pin_config.get("class", "LED"))
            self._out_pins[pin] = cls(pin, **pin_config.get("kwargs", {}))
        elif direction == PinDirection.INPUT:
            cls = getattr(self.io, pin_config.get("class", "Button"))
            pin_config.setdefault("pull_up", self.pullup_map[pullup])
            pin_config.setdefault(
                "active_state", True if pin_config["pull_up"] is None else None
            )
            pin_config.setdefault("initial_value", initial)
            self._in_pins[pin] = cls(pin, **pin_config.get("kwargs", {}))
        else:
            raise ValueError("Invalid PinDirection")

    def set_pin(self, pin: PinType, value: bool) -> None:
        if value:
            self._out_pins[pin].on()
        else:
            self._out_pins[pin].off()

    def get_pin(self, pin: PinType) -> bool:
        return cast(bool, self._in_pins[pin].is_active)

    def setup_interrupt_callback(
        self,
        pin: PinType,
        edge: InterruptEdge,
        in_conf: ConfigType,
        callback: Callable[[List[Any], Dict[Any, Any]], None],
    ) -> None:
        _LOG.debug(
            "Added interrupt to gpiozero Pi pin '%s' with callback '%s'", pin, callback
        )

        if edge in (InterruptEdge.BOTH, InterruptEdge.RISING):
            self._in_pins[pin].when_activated = partial(callback, True)
        if edge in (InterruptEdge.BOTH, InterruptEdge.FALLING):
            self._in_pins[pin].when_deactivated = partial(callback, False)
        self.interrupt_edges[pin] = edge

    def get_interrupt_value(self, pin: PinType, *args: Any, **kwargs: Any) -> bool:
        return cast(bool, args[0])
