import mock
import pytest

from pi_mqtt_gpio import server

@mock.patch("pkg_resources.WorkingSet")
def test_imr_no_attribute(mock_ws):
    """
    Should not bother looking up what's installed when there's no requirements.
    """
    module = object()
    server.install_missing_requirements(module)
    mock_ws.assert_not_called()
