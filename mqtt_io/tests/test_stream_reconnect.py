"""A missing stream device is opened again without blocking the others."""

from typing import Optional

from mqtt_io.modules.stream import GenericStream


class _FlakyStream(GenericStream):
    """Fails the first open, then succeeds."""

    def __init__(self) -> None:
        self.opens = 0
        super().__init__({})

    def setup_module(self) -> None:
        self.opens += 1
        if self.opens == 1:
            raise RuntimeError("device missing")

    def read(self) -> Optional[bytes]:
        return None

    def write(self, data: bytes) -> None:
        return None


def test_reconnect_opens_a_device_that_was_missing_at_startup() -> None:
    """Setup failure is logged and a later reconnect opens the device."""
    stream = _FlakyStream()
    try:
        assert stream.opens == 1
        stream.reconnect()
        assert stream.opens == 2
    finally:
        stream.executor.shutdown(wait=False)
