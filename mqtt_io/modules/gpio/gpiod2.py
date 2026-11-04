"""
Linux Kernel 5.10+ libgpiod (v2 Python bindings)
"""
import threading
from datetime import timedelta
from typing import TYPE_CHECKING, Any, Callable, Dict, Optional

from ...types import ConfigType, PinType
from . import GenericGPIO, InterruptEdge, InterruptSupport, PinDirection, PinPUD

if TYPE_CHECKING:
    # pylint: disable=import-error
    import gpiod  # type: ignore

# Official libgpiod Python bindings (v2 API). Requires Linux kernel >= 5.10.
REQUIREMENTS = ("gpiod>=2.0.0",)

CONFIG_SCHEMA = {
    "chip": {"type": "string", "required": False, "default": "/dev/gpiochip0"}
}

CONSUMER = "mqtt-io"


class GPIO(GenericGPIO):  # pylint: disable=too-many-instance-attributes
    """
    Implementation of GPIO class for libgpiod v2 (linux kernel >= 5.10).
    Use the `gpiod` module instead on older kernels.
    """

    INTERRUPT_SUPPORT = InterruptSupport.SOFTWARE_CALLBACK

    def setup_module(self) -> None:
        # pylint: disable=import-outside-toplevel,import-error
        import gpiod
        from gpiod.line import Bias, Direction, Edge  # type: ignore

        self.io = gpiod
        self.chip_path: str = self.config["chip"]
        self.pins: Dict[PinType, "gpiod.LineRequest"] = {}
        self.line_settings: Dict[PinType, "gpiod.LineSettings"] = {}
        self.interrupt_threads: Dict[PinType, threading.Thread] = {}
        self.stop_event = threading.Event()
        # get_value/set_value share per-request scratch buffers in the C extension
        # and release the GIL, so serialise them across executor threads. The
        # interrupt thread only polls the fd and reads into a separate event
        # buffer, so it doesn't need this lock.
        self.io_lock = threading.Lock()

        self.direction_map = {
            PinDirection.INPUT: Direction.INPUT,
            PinDirection.OUTPUT: Direction.OUTPUT,
        }

        self.pullup_map = {
            PinPUD.OFF: Bias.DISABLED,
            PinPUD.UP: Bias.PULL_UP,
            PinPUD.DOWN: Bias.PULL_DOWN,
        }

        self.interrupt_edge_map = {
            InterruptEdge.RISING: Edge.RISING,
            InterruptEdge.FALLING: Edge.FALLING,
            InterruptEdge.BOTH: Edge.BOTH,
        }

    def _value(self, value: bool) -> "gpiod.line.Value":
        line_value = self.io.line.Value
        return line_value.ACTIVE if value else line_value.INACTIVE

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
        pin:        offset of the gpio line on the chip
        direction:  input or output
        pullup:     bias setting (requires Linux kernel >= 5.5 and driver support)
        """
        settings = self.io.LineSettings(
            direction=self.direction_map[direction],
            bias=self.pullup_map[pullup],
        )

        if direction == PinDirection.OUTPUT:
            if initial is not None:
                settings.output_value = self._value(initial == "high")
            else:
                # Initial value not provided by config. Read the current value and
                # keep it to avoid glitching the output: request the line "as-is"
                # first, read it, release it, then request it as an output.
                with self.io.request_lines(
                    self.chip_path,
                    consumer=CONSUMER,
                    config={pin: self.io.LineSettings()},
                ) as as_is_request:
                    settings.output_value = as_is_request.get_value(pin)

        self.pins[pin] = self.io.request_lines(
            self.chip_path, consumer=CONSUMER, config={pin: settings}
        )
        self.line_settings[pin] = settings

    def setup_interrupt_callback(
        self,
        pin: PinType,
        edge: InterruptEdge,
        in_conf: ConfigType,
        callback: Callable[..., None],
    ) -> None:
        """
        Install interrupt callback function
        pin:        gpio to watch for interrupts
        edge:       triggering edge: RISING, FALLING or BOTH
        callback:   the callback function to be called, when interrupt occurs
        bouncetime: minimum time between two interrupts
        """
        settings = self.line_settings[pin]
        settings.edge_detection = self.interrupt_edge_map[edge]
        request = self.pins[pin]
        request.reconfigure_lines({pin: settings})

        bouncetime: int = in_conf["bouncetime"]
        int_thread = InterruptThread(
            request, callback, bouncetime, self.stop_event, self.io
        )
        int_thread.start()
        self.interrupt_threads[pin] = int_thread

    def get_interrupt_value(self, pin: PinType, *args: Any, **kwargs: Any) -> bool:
        # We established the pin's value in the InterruptThread, so we just give it back
        pin_value: bool = kwargs["pin_value"]
        return pin_value

    def set_pin(self, pin: PinType, value: bool) -> None:
        with self.io_lock:
            self.pins[pin].set_value(pin, self._value(value))

    def get_pin(self, pin: PinType) -> bool:
        with self.io_lock:
            value = self.pins[pin].get_value(pin)
        return bool(value == self.io.line.Value.ACTIVE)

    def cleanup(self) -> None:
        self.stop_event.set()
        for thread in self.interrupt_threads.values():
            thread.join(timeout=10)
        for request in self.pins.values():
            request.release()
        self.pins.clear()


class InterruptThread(threading.Thread):
    """
    Thread that waits on edge events for a given line request, then calls the callback.
    """

    def __init__(
        self,
        request: "gpiod.LineRequest",
        callback: Callable[..., None],
        bouncetime: int,
        stop_event: threading.Event,
        io: Any,
    ):
        super().__init__()
        self.daemon = True

        self.request = request
        self.callback = callback
        self.bouncetime_ns = bouncetime * 1_000_000
        self.stop_event = stop_event
        self.rising_edge = io.EdgeEvent.Type.RISING_EDGE

    def run(self) -> None:
        previous_event_ns: Optional[int] = None
        while not self.stop_event.is_set():
            if not self.request.wait_edge_events(timedelta(seconds=2)):
                continue
            for event in self.request.read_edge_events():
                # Kernel timestamps (CLOCK_MONOTONIC) are used for debouncing
                if (
                    previous_event_ns is not None
                    and event.timestamp_ns - previous_event_ns < self.bouncetime_ns
                ):
                    continue
                previous_event_ns = event.timestamp_ns
                self.callback(pin_value=event.event_type == self.rising_edge)
