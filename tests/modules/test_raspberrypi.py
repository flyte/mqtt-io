import pytest

from pi_mqtt_gpio.modules import raspberrypi, PinDirection, PinPullup

#global gpio
gpio = 0

'''
This tests need hardware wiring gpio 26 with gpio 21.
You may connect them with a 10kOhm resistor
'''

def test_raspberrypi_init():
    # init the raspberrypi gpios
    global gpio
    gpio = raspberrypi.GPIO("")

def test_raspberrypi_setup_pin():
    # setup gpio 26 as output and gpio 21 as input without pullup
    global gpio
    config = {'initial' : None}
    gpio.setup_pin(26, PinDirection.OUTPUT, None, config)
    gpio.setup_pin(21, PinDirection.INPUT, PinPullup.OFF, config)
    
    
def test_raspberrypi_set_pin():
    # set the value of pin 26 high
    gpio.set_pin(26, True)
    
def test_raspberrypi_get_pin():
    # get the value of the connected input
    value = gpio.get_pin(21)
    assert value == True

def test_raspberrypi_low_high():
    # set gpio 26 low
    gpio.set_pin(26, False)
    value = gpio.get_pin(21)
    assert value == False
    #set gpio 26 high
    gpio.set_pin(26, True)
    value = gpio.get_pin(21)
    assert value == True
    # set gpio 26 low again
    gpio.set_pin(26, False)
    value = gpio.get_pin(21)
    assert value == False

def test_raspberrypi_cleanup():
    # cleanup gpios for next test
    gpio.cleanup()

















