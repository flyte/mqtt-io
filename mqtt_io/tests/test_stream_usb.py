"""Regression tests for USB stream cleanup."""

import sys
from typing import Any, Dict
from unittest.mock import MagicMock, patch

from mqtt_io.modules.stream.usb import Stream


def test_cleanup_releases_configured_interface_once_then_disposes() -> None:
    """cleanup releases the configured interface once, then disposes the device."""
    interface = 1
    config: Dict[str, Any] = {
        "vid": 0x0525,
        "pid": 0xA4AC,
        "read_size": 1024,
        "read_timeout": 1,
        "write_size": 64,
        "interface": interface,
    }

    mock_usb = MagicMock()
    mock_core = MagicMock()
    mock_util = MagicMock()
    mock_usb.core = mock_core
    mock_usb.util = mock_util

    device = MagicMock(name="device")
    cfg = MagicMock()
    cfg.__getitem__.return_value = MagicMock()
    device.get_active_configuration.return_value = cfg
    mock_core.find.return_value = device
    mock_util.find_descriptor.side_effect = [
        MagicMock(name="epIn"),
        MagicMock(name="epOut"),
    ]

    with patch.dict(
        sys.modules, {"usb": mock_usb, "usb.core": mock_core, "usb.util": mock_util}
    ):
        stream = Stream(config)
        stream.cleanup()

    mock_util.release_interface.assert_called_once_with(device, interface)
    mock_util.dispose_resources.assert_called_once_with(device)
