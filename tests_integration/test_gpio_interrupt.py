import mock
import pytest

from pi_mqtt_gpio import server
from pi_mqtt_gpio.server import GPIO_INTERRUPT_LOOKUP
from pi_mqtt_gpio.modules.stdio import GPIO

@pytest.fixture
def fix_interrupt():
    GPIO_INTERRUPT_LOOKUP.clear()
    yield fix_interrupt

@mock.patch("pi_mqtt_gpio.modules.stdio.GPIO")
def test_server_gpio_configure_gpio_module(mock_std_gpio):
    """
    check stdio configure module
    """
    gpio_config = {"name": "dev", "module": "stdio", "cleanup": False}
    server.configure_gpio_module(gpio_config)
    mock_std_gpio.assert_called()

@mock.patch("pi_mqtt_gpio.modules.stdio.GPIO")
def test_server_gpio_initialise_digital_input(mock_std_gpio):
    """
    check stdio input
    """
    in_conf = {"name": "button", "module": "dev", "pin": 21, "on_payload": "ON",
               "off_payload": "OFF", "pullup": False, "pulldown": True,
               "interrupt": "none", "bouncetime": 100}
    server.initialise_digital_input(in_conf, mock_std_gpio)
    mock_std_gpio.setup_pin.assert_called()
    mock_std_gpio.setup_interrupt.assert_not_called()

@mock.patch("pi_mqtt_gpio.modules.stdio.GPIO")
def test_server_gpio_initialise_digital_input_interrupt(mock_std_gpio, fix_interrupt):
    """	
    check stdio input with interrupt
    """
    in_conf = {"name": "button", "module": "dev", "pin": 21, "on_payload": "ON",
               "off_payload": "OFF", "pullup": False, "pulldown": True,
               "interrupt": "rising", "bouncetime": 100}
    server.initialise_digital_input(in_conf, mock_std_gpio)
    mock_std_gpio.setup_pin.assert_called()
    mock_std_gpio.setup_interrupt.assert_called()
    assert GPIO_INTERRUPT_LOOKUP["dev"][21] == in_conf
