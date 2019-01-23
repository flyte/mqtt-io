import pytest

from pi_mqtt_gpio.modules import stdio, PinDirection, PinPullup

# global gpio
gpio = 0

def test_stdio_init():
    """
    Should not bother looking up what's installed when there's no requirements.
    """
    global gpio
    gpio = stdio.GPIO("")

def test_stdio_setup_pin():
    """
    Should not bother looking up what's installed when there's no requirements.
    """
    global gpio
    config = {'initial' : None}
    gpio.setup_pin(5, PinDirection.INPUT, PinPullup.OFF, config)
    
    
def test_stdio_set_pin():
    """
    Should not bother looking up what's installed when there's no requirements.
    """
    global gpio
    gpio.set_pin(5, True)
    
def test_stdio_get_pin():
    """
    Should not bother looking up what's installed when there's no requirements.
    """
    global gpio
    value = gpio.get_pin(5)
    assert value == False
