"""
Linux Kernel 4.8+ libgpiod
"""
import threading
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any, Callable, Dict, Optional

from ...types import ConfigType, PinType
from . import GenericGPIO, InterruptEdge, InterruptSupport, PinDirection, PinPUD

if TYPE_CHECKING:
    # pylint: disable=import-error
    import gpiod  # type: ignore

# Requires libgpiod-devel, libgpiod
REQUIREMENTS = ("gpiod",)

CONFIG_SCHEMA = {
    "chip": {"type": "string", "required": False, "default": "/dev/gpiochip0"}
}


class GPIO(GenericGPIO):  # pylint: disable=too-many-instance-attributes
    """
    Implementation of GPIO class for libgpiod (linux kernel >= 4.8).
    """

    INTERRUPT_SUPPORT = InterruptSupport.SOFTWARE_CALLBACK

    def setup_module(self) -> None:
        # pylint: disable=import-outside-toplevel,import-error
        import gpiod

        self.io: gpiod = gpiod
        self.chip = gpiod.chip(self.config["chip"])
        self.pins: Dict[PinType, gpiod.line] = {}
        self.interrupt_threads: Dict[PinType, threading.Thread] = {}
        self.stop_event = threading.Event()

        self.direction_map = {
            PinDirection.INPUT: gpiod.line_request.DIRECTION_INPUT,
            PinDirection.OUTPUT: gpiod.line_request.DIRECTION_OUTPUT,
        }

        self.flags_map = {
            PinPUD.OFF: gpiod.line_request.FLAG_BIAS_DISABLE,
            PinPUD.UP: gpiod.line_request.FLAG_BIAS_PULL_UP,
            PinPUD.DOWN: gpiod.line_request.FLAG_BIAS_PULL_DOWN,
        }

        self.interrupt_edge_map = {
            InterruptEdge.RISING: gpiod.line_request.EVENT_RISING_EDGE,
            InterruptEdge.FALLING: gpiod.line_request.EVENT_FALLING_EDGE,
            InterruptEdge.BOTH: gpiod.line_request.EVENT_BOTH_EDGES,
        }

    def setup_pin(
        self,
        pin: PinType,
        direction: PinDirection,
        pullup: PinPUD,
        pin_config: ConfigType,
        initial: Optional[str] = None,
    ) -> None:
        """
        Setup a pin as either input or output.
        pin:        offset to use the gpio line
        direction:  input or output
        pullup:     pullup settings are not supported
        """
        # Pullup settings are called bias in libgpiod and are only
        # available since Linux Kernel 5.5.

        line: "gpiod.line" = self.chip.get_line(pin)

        line_request = self.io.line_request()
        line_request.consumer = "mqtt-io"
        line_request.request_type = self.direction_map[direction]
        line_request.flags = self.flags_map[pullup]

        if direction == PinDirection.OUTPUT:
            if initial is not None:
                # Set default_val = Initial value provided by config
                line.request(line_request, 1 if initial == "high" else 0)
            else:
                # Initial value not provided by config
                # We need to read current value and keep it to avoid inconsistency
                # So we request line "as-is" first to get current value
                as_is_line_request = self.io.line_request()
                as_is_line_request.consumer = line_request.consumer
                as_is_line_request.request_type = self.io.line_request.DIRECTION_AS_IS
                line.request(as_is_line_request)
                current_value = line.get_value()
                line.release()

                # And request line again with default_val=current_value
                line.request(line_request, current_value)
        else:
            line.request(line_request)

        self.pins[pin] = line

    def setup_interrupt_callback(
        self,
        pin: PinType,
        edge: InterruptEdge,
        in_conf: ConfigType,
        callback: Callable[..., None],
    ) -> None:
        """
        Install interrupt callback function
        handle:     is returned in the callback function as identification
        pin:        gpio to watch for interrupts
        edge:       triggering edge: RISING, FALLING or BOTH
        callback:   the callback function to be called, when interrupt occurs
        bouncetime: minimum time between two interrupts
        """

        line_request = self.io.line_request()
        line_request.consumer = "mqtt-io"
        line_request.request_type = self.interrupt_edge_map[edge]

        bouncetime: int = in_conf["bouncetime"]
        int_thread = InterruptThread(
            self.chip, pin, line_request, callback, bouncetime, self.stop_event
        )
        int_thread.start()
        self.interrupt_threads[pin] = int_thread

    def get_interrupt_value(self, pin: PinType, *args: Any, **kwargs: Any) -> bool:
        # We established the pin's value in the InterruptThread, so we just give it back
        pin_value: bool = kwargs["pin_value"]
        return pin_value

    def set_pin(self, pin: PinType, value: bool) -> None:
        self.pins[pin].set_value(value)

    def get_pin(self, pin: PinType) -> bool:
        return bool(self.pins[pin].get_value())

    def cleanup(self) -> None:
        self.stop_event.set()
        for thread in self.interrupt_threads.values():
            thread.join(timeout=10)


class InterruptThread(threading.Thread):
    """
    Thread that waits on interrupt events for a given pin, then calls the callback.
    """

    def __init__(
        self,
        chip: "gpiod.chip",
        pin: PinType,
        line_request: "gpiod.line_request",
        callback: Callable[..., None],
        bouncetime: int,
        stop_event: threading.Event,
    ):
        super().__init__()
        self.daemon = True

        self.pin = pin
        self.line: "gpiod.line" = chip.get_line(self.pin)
        self.line.release()
        self.line.request(line_request)
        self.callback = callback
        self.bouncetime = timedelta(milliseconds=bouncetime)
        self.stop_event = stop_event

    def run(self) -> None:
        # pylint: disable=import-outside-toplevel,import-error
        import gpiod

        previous_event_time = datetime.now()
        while not self.stop_event.is_set():
            if not self.line.event_wait(timedelta(seconds=2)):
                continue
            event: gpiod.line_event = self.line.event_read()
            now = datetime.now()
            if now - previous_event_time < self.bouncetime:
                continue
            previous_event_time = now
            pin_value = None
            if event.event_type == gpiod.line_request.EVENT_RISING_EDGE:
                pin_value = True
            elif event.event_type == gpiod.line_request.EVENT_FALLING_EDGE:
                pin_value = False
            if pin_value is None:
                # Poll the pin for its value :(
                pin_value = bool(self.line.get_value())
            self.callback(pin_value=pin_value)
