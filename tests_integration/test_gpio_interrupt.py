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
    Should not bother looking up what's installed when there's no requirements.
    """
    gpio_config = {"name": "dev", "module": "stdio", "cleanup": False}
    server.configure_gpio_module(gpio_config)
    mock_std_gpio.assert_called()

@mock.patch("pi_mqtt_gpio.modules.stdio.GPIO")
def test_server_gpio_initialise_digital_input(mock_std_gpio):
    """
    Should not bother looking up what's installed when there's no requirements.
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
    Should not bother looking up what's installed when there's no requirements.
    """
    in_conf = {"name": "button", "module": "dev", "pin": 21, "on_payload": "ON",
               "off_payload": "OFF", "pullup": False, "pulldown": True,
               "interrupt": "rising", "bouncetime": 100}
    server.initialise_digital_input(in_conf, mock_std_gpio)
    mock_std_gpio.setup_pin.assert_called()
    mock_std_gpio.setup_interrupt.assert_called()
    assert GPIO_INTERRUPT_LOOKUP["dev"][21] == in_conf
    
@mock.patch("pi_mqtt_gpio.server.client")
def test_server_gpio_initialise_digital_input_interrupt_trigger(mock_client, fix_interrupt):
    """
    Should not bother looking up what's installed when there's no requirements.
    """
    in_conf = {"name": "button", "module": "dev", "pin": 21, "on_payload": "ON",
               "off_payload": "OFF", "pullup": False, "pulldown": True,
               "retain" : False, "interrupt": "rising", "bouncetime": 100}
    GPIO_INTERRUPT_LOOKUP["dev"] = {}
    GPIO_INTERRUPT_LOOKUP["dev"][21] = in_conf
    server.gpio_interrupt_callback("dev", 21, True)
    mock_client.publish.assert_called_once_with(
        "%s/%s/%s" % (server.topic_prefix, server.OUTPUT_TOPIC, in_conf["name"]),
        payload=True,
        retain=in_conf["retain"])
