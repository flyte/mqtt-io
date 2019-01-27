import pytest
import time
from pi_mqtt_gpio.modules import raspberrypi, PinDirection, PinPullup, InterruptEdge

#global gpio
gpio = 0
interrupt_count = 0

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

def test_raspberrypi_interrupt_setup_pin():
    # setup outputs and inputs for interrupt tests
    global gpio
    # configs
    config_output = {'initial' : "low"}
    config_input = {}

    #f or rising edges
    gpio.setup_pin(19, PinDirection.OUTPUT, None, config_output)
    gpio.setup_pin(20, PinDirection.INPUT, PinPullup.UP, config_input)
    gpio.setup_interrupt(20, InterruptEdge.RISING, gpio_testcallback, 300)

    # for falling edges
    gpio.setup_pin(13, PinDirection.OUTPUT, None, config_output)
    gpio.setup_pin(16, PinDirection.INPUT, PinPullup.DOWN, config_input)
    #gpio.setup_interrupt(16, InterruptEdge.FALLING, gpio_testcallback, 300)

    # for both edges
    gpio.setup_pin(6, PinDirection.OUTPUT, None, config_output)
    gpio.setup_pin(12, PinDirection.INPUT, PinPullup.OFF, config_input)
    gpio.setup_interrupt(12, InterruptEdge.BOTH, gpio_testcallback)

def gpio_testcallback(pin):
    '''
    callback function for test interrupts
    '''
    global interrupt_count
    interrupt_count = interrupt_count + 1
    # debug output: 
    # print "\ngpio_testcallback called for pin %d" % (pin)

def test_raspberrypi_interrupt_trigger_rising_single():
    # set gpio 19 low
    global interrupt_count
    interrupt_count = 0
    gpio.set_pin(19, True)  # one rising edge
    time.sleep(0.5)  # wait to callback function happens
    assert interrupt_count == 1

def test_raspberrypi_interrupt_trigger_rising_multi():
    # set gpio 19 low
    global interrupt_count
    gpio.set_pin(19, False)  # reset low
    time.sleep(0.5)  # wait if bouncetime is still active

    interrupt_count = 0
    gpio.set_pin(19, True)  # one rising edge
    gpio.set_pin(19, False)  # reset low
    time.sleep(0.3)  # wait bounce time
    gpio.set_pin(19, True)  # one rising edge
    gpio.set_pin(19, False)  # reset low
    time.sleep(0.3)  # wait bounce time
    gpio.set_pin(19, True)  # one rising edge
    gpio.set_pin(19, False)  # reset low
    time.sleep(0.3)  # wait bounce time
    assert interrupt_count == 3
    
def test_raspberrypi_interrupt_trigger_rising_bouncetime():
    # set gpio 19 low
    global interrupt_count
    gpio.set_pin(19, False)  # reset low
    time.sleep(0.5)  # wait if bouncetime is still active

    # generate one interrupt
    interrupt_count = 0
    gpio.set_pin(19, True)  # one rising edge
    gpio.set_pin(19, False)  # reset low
    time.sleep(0.01)  # wait to callback function happens
    assert interrupt_count == 1
    
    # miss one interrupt
    time.sleep(0.1)  # wait less time than bounce time
    gpio.set_pin(19, True)  # one rising edge
    gpio.set_pin(19, False)  # reset low
    time.sleep(0.01)  # wait to callback function happens
    assert interrupt_count == 1  # interrupt should not be called
    
    #take a new interrupt
    time.sleep(0.3)  # wait bounce time
    gpio.set_pin(19, True)  # one rising edge
    gpio.set_pin(19, False)  # reset low
    time.sleep(0.01)  # wait to callback function happens
    assert interrupt_count == 2 # take this interrupt

def test_raspberrypi_interrupt_trigger_falling_single():
    global interrupt_count
    interrupt_count = 0
    gpio.set_pin(13, True)  # set output high
    time.sleep(0.5)  # wait to callback function happens
    assert interrupt_count == 0 # should not happen on rising edge
    
    gpio.set_pin(13, False)  # set output low
    time.sleep(0.5)  # wait to callback function happens
    assert interrupt_count == 1 # should not happen on rising edge
    
def test_raspberrypi_interrupt_trigger_both_single():
    global interrupt_count
    interrupt_count = 0
    gpio.set_pin(6, True)  # set output high
    time.sleep(0.5)  # wait to callback function happens
    assert interrupt_count == 1 # should not happen on rising edge
    
    gpio.set_pin(6, False)  # set output low
    time.sleep(0.5)  # wait to callback function happens
    assert interrupt_count == 2 # should not happen on rising edge
    
def test_raspberrypi_cleanup():
    # cleanup gpios for next test
    gpio.cleanup()

















