import pytest
import time
from pi_mqtt_gpio.modules import raspberrypi, PinDirection, PinPullup, InterruptEdge


pytestmark = pytest.mark.hw_raspberrypi

'''
Attention: 
The following tests will only work with hardware modifikations.
Definition of wired connected GPIOs, always connect xxx_OUTPUT
with xxx_INPUT. You may connect them with a 10kOhm resistor.
'''
# gpio pins for get and set
TEST_RASPBERRYPI_GPIO_SET_GET_OUTPUT = 26
TEST_RASPBERRYPI_GPIO_SET_GET_INPUT  = 21

# gpio pins interrupt tests
TEST_RASPBERRYPI_GPIO_INTERRUPT_RISING_OUTPUT  = 19
TEST_RASPBERRYPI_GPIO_INTERRUPT_RISING_INPUT   = 20
TEST_RASPBERRYPI_GPIO_INTERRUPT_FALLING_OUTPUT = 13
TEST_RASPBERRYPI_GPIO_INTERRUPT_FALLING_INPUT  = 16
TEST_RASPBERRYPI_GPIO_INTERRUPT_BOTH_OUTPUT    = 6
TEST_RASPBERRYPI_GPIO_INTERRUPT_BOTH_INPUT     = 12

# global gpio and interrupt callback function
gpio = None
interrupt_count = 0
test_handle = 0

# Use this function for each testcase
@pytest.fixture(autouse=True)
def fix_raspberrypi_setup_teardown():
    # initialize gpios and counter for interrupt before each test case
    global gpio
    gpio = raspberrypi.GPIO("")
    global interrupt_count
    interrupt_count = 0

    # run the test case here
    yield

    # clean up the gpios after each test
    gpio.cleanup()

def gpio_testcallback(handle, pin, value):
    '''
    callback function for test interrupts, count the calls of this function
    and store a given handle.
    '''
    global interrupt_count
    interrupt_count = interrupt_count + 1
    global test_handle
    test_handle = handle

def test_raspberrypi_setup_output_pin():
    # setup a output gpio
    gpio.setup_pin(TEST_RASPBERRYPI_GPIO_SET_GET_OUTPUT, PinDirection.OUTPUT, None, {'initial' : None})

def test_raspberrypi_setup_input_pin():
    # setup a input gpio
    gpio.setup_pin(TEST_RASPBERRYPI_GPIO_SET_GET_INPUT, PinDirection.INPUT, PinPullup.OFF, {})

def test_raspberrypi_set_pin():
    # setup a output gpio and set value to high
    gpio.setup_pin(TEST_RASPBERRYPI_GPIO_SET_GET_OUTPUT, PinDirection.OUTPUT, None, {'initial' : None})
    gpio.set_pin(TEST_RASPBERRYPI_GPIO_SET_GET_OUTPUT, True)
    
def test_raspberrypi_get_pin():
    # setup a output and input gpio and read the value from input
    gpio.setup_pin(TEST_RASPBERRYPI_GPIO_SET_GET_OUTPUT, PinDirection.OUTPUT, None, {'initial' : None})
    gpio.setup_pin(TEST_RASPBERRYPI_GPIO_SET_GET_INPUT, PinDirection.INPUT, PinPullup.OFF, {})
    # get the value of the connected input
    value = gpio.get_pin(TEST_RASPBERRYPI_GPIO_SET_GET_INPUT)
    assert value == True

def test_raspberrypi_low_high():
    # setup a output gpio and set value to low and high
    gpio.setup_pin(TEST_RASPBERRYPI_GPIO_SET_GET_OUTPUT, PinDirection.OUTPUT, None, {'initial' : 'high'})
    gpio.setup_pin(TEST_RASPBERRYPI_GPIO_SET_GET_INPUT, PinDirection.INPUT, PinPullup.OFF, {})
    # set gpio TEST_RASPBERRYPI_GPIO_SET_GET_OUTPUT low
    gpio.set_pin(TEST_RASPBERRYPI_GPIO_SET_GET_OUTPUT, False)
    value = gpio.get_pin(TEST_RASPBERRYPI_GPIO_SET_GET_INPUT)
    assert value == False
    #set gpio TEST_RASPBERRYPI_GPIO_SET_GET_OUTPUT high
    gpio.set_pin(TEST_RASPBERRYPI_GPIO_SET_GET_OUTPUT, True)
    value = gpio.get_pin(TEST_RASPBERRYPI_GPIO_SET_GET_INPUT)
    assert value == True
    # set gpio TEST_RASPBERRYPI_GPIO_SET_GET_OUTPUT low again
    gpio.set_pin(TEST_RASPBERRYPI_GPIO_SET_GET_OUTPUT, False)
    value = gpio.get_pin(TEST_RASPBERRYPI_GPIO_SET_GET_INPUT)
    assert value == False

def test_raspberrypi_interrupt_callback_handle():
    # test for handle passing
    gpio.setup_pin(TEST_RASPBERRYPI_GPIO_INTERRUPT_RISING_OUTPUT, PinDirection.OUTPUT, None, {'initial' : "low"})
    gpio.setup_pin(TEST_RASPBERRYPI_GPIO_INTERRUPT_RISING_INPUT, PinDirection.INPUT, PinPullup.UP, {})
    gpio.io.remove_event_detect(TEST_RASPBERRYPI_GPIO_INTERRUPT_RISING_INPUT)
    gpio.setup_interrupt("myhandle", TEST_RASPBERRYPI_GPIO_INTERRUPT_RISING_INPUT, InterruptEdge.RISING, gpio_testcallback, 300)

    gpio.set_pin(TEST_RASPBERRYPI_GPIO_INTERRUPT_RISING_OUTPUT, True)  # one rising edge
    time.sleep(0.1)  # wait to callback function happens
    assert interrupt_count == 1
    assert test_handle == "myhandle"
    
def test_raspberrypi_interrupt_trigger_rising_single():
    # setup outputs and inputs for interrupt tests for rising edges
    gpio.setup_pin(TEST_RASPBERRYPI_GPIO_INTERRUPT_RISING_OUTPUT, PinDirection.OUTPUT, None, {'initial' : "low"})
    gpio.setup_pin(TEST_RASPBERRYPI_GPIO_INTERRUPT_RISING_INPUT, PinDirection.INPUT, PinPullup.UP, {})
    gpio.io.remove_event_detect(TEST_RASPBERRYPI_GPIO_INTERRUPT_RISING_INPUT)
    gpio.setup_interrupt(None, TEST_RASPBERRYPI_GPIO_INTERRUPT_RISING_INPUT, InterruptEdge.RISING, gpio_testcallback, 300)

    gpio.set_pin(TEST_RASPBERRYPI_GPIO_INTERRUPT_RISING_OUTPUT, True)  # one rising edge
    time.sleep(0.1)  # wait to callback function happens
    assert interrupt_count == 1

def test_raspberrypi_interrupt_trigger_rising_multi():
    # setup outputs and inputs for interrupt tests for multiple rising edges
    gpio.setup_pin(TEST_RASPBERRYPI_GPIO_INTERRUPT_RISING_OUTPUT, PinDirection.OUTPUT, None, {'initial' : "low"})
    gpio.setup_pin(TEST_RASPBERRYPI_GPIO_INTERRUPT_RISING_INPUT, PinDirection.INPUT, PinPullup.UP, {})
    gpio.io.remove_event_detect(TEST_RASPBERRYPI_GPIO_INTERRUPT_RISING_INPUT)
    gpio.setup_interrupt(None, TEST_RASPBERRYPI_GPIO_INTERRUPT_RISING_INPUT, InterruptEdge.RISING, gpio_testcallback, 300)

    gpio.set_pin(TEST_RASPBERRYPI_GPIO_INTERRUPT_RISING_OUTPUT, True)  # one rising edge
    gpio.set_pin(TEST_RASPBERRYPI_GPIO_INTERRUPT_RISING_OUTPUT, False)  # reset low
    time.sleep(0.4)  # wait bounce time
    gpio.set_pin(TEST_RASPBERRYPI_GPIO_INTERRUPT_RISING_OUTPUT, True)  # one rising edge
    gpio.set_pin(TEST_RASPBERRYPI_GPIO_INTERRUPT_RISING_OUTPUT, False)  # reset low
    time.sleep(0.4)  # wait bounce time
    gpio.set_pin(TEST_RASPBERRYPI_GPIO_INTERRUPT_RISING_OUTPUT, True)  # one rising edge
    gpio.set_pin(TEST_RASPBERRYPI_GPIO_INTERRUPT_RISING_OUTPUT, False)  # reset low
    time.sleep(0.3)  # wait bounce time
    assert interrupt_count == 3
    
def test_raspberrypi_interrupt_trigger_rising_bouncetime():
    # test for bouncetime, miss one interrupt durring bounce time
    gpio.setup_pin(TEST_RASPBERRYPI_GPIO_INTERRUPT_RISING_OUTPUT, PinDirection.OUTPUT, None, {'initial' : "low"})
    gpio.setup_pin(TEST_RASPBERRYPI_GPIO_INTERRUPT_RISING_INPUT, PinDirection.INPUT, PinPullup.UP, {})
    gpio.io.remove_event_detect(TEST_RASPBERRYPI_GPIO_INTERRUPT_RISING_INPUT)
    gpio.setup_interrupt(None, TEST_RASPBERRYPI_GPIO_INTERRUPT_RISING_INPUT, InterruptEdge.RISING, gpio_testcallback, 300)

    # generate one interrupt
    gpio.set_pin(TEST_RASPBERRYPI_GPIO_INTERRUPT_RISING_OUTPUT, True)  # one rising edge
    gpio.set_pin(TEST_RASPBERRYPI_GPIO_INTERRUPT_RISING_OUTPUT, False)  # reset low
    time.sleep(0.1)  # wait to callback function happens
    assert interrupt_count == 1
    
    # miss one interrupt
    time.sleep(0)  # wait less time than bounce time
    gpio.set_pin(TEST_RASPBERRYPI_GPIO_INTERRUPT_RISING_OUTPUT, True)  # one rising edge
    gpio.set_pin(TEST_RASPBERRYPI_GPIO_INTERRUPT_RISING_OUTPUT, False)  # reset low
    time.sleep(0.1)  # wait to callback function happens
    assert interrupt_count == 1  # interrupt should not be called
    
    #take a new interrupt
    time.sleep(0.3)  # wait bounce time
    gpio.set_pin(TEST_RASPBERRYPI_GPIO_INTERRUPT_RISING_OUTPUT, True)  # one rising edge
    gpio.set_pin(TEST_RASPBERRYPI_GPIO_INTERRUPT_RISING_OUTPUT, False)  # reset low
    time.sleep(0.1)  # wait to callback function happens
    assert interrupt_count == 2 # take this interrupt

def test_raspberrypi_interrupt_trigger_falling_single():
    # setup outputs and inputs for interrupt tests for falling edges
    gpio.setup_pin(TEST_RASPBERRYPI_GPIO_INTERRUPT_FALLING_OUTPUT, PinDirection.OUTPUT, None, {'initial' : "high"})
    gpio.setup_pin(TEST_RASPBERRYPI_GPIO_INTERRUPT_FALLING_INPUT, PinDirection.INPUT, PinPullup.DOWN, {})
    gpio.io.remove_event_detect(TEST_RASPBERRYPI_GPIO_INTERRUPT_FALLING_INPUT)
    gpio.setup_interrupt(None, TEST_RASPBERRYPI_GPIO_INTERRUPT_FALLING_INPUT, InterruptEdge.FALLING, gpio_testcallback, 300)

    gpio.set_pin(TEST_RASPBERRYPI_GPIO_INTERRUPT_FALLING_OUTPUT, True)  # set output high
    time.sleep(0.1)  # wait to callback function happens
    assert interrupt_count == 0 # should not happen on rising edge
    
    gpio.set_pin(TEST_RASPBERRYPI_GPIO_INTERRUPT_FALLING_OUTPUT, False)  # set output low
    time.sleep(0.1)  # wait to callback function happens
    assert interrupt_count == 1 # should not happen on rising edge
    
def test_raspberrypi_interrupt_trigger_both_single():
    # test for rising and falling edge configuration
    gpio.setup_pin(TEST_RASPBERRYPI_GPIO_INTERRUPT_BOTH_OUTPUT, PinDirection.OUTPUT, None, {'initial' : "low"})
    gpio.setup_pin(TEST_RASPBERRYPI_GPIO_INTERRUPT_BOTH_INPUT, PinDirection.INPUT, PinPullup.OFF, {})
    gpio.io.remove_event_detect(TEST_RASPBERRYPI_GPIO_INTERRUPT_BOTH_INPUT)
    gpio.setup_interrupt(None, TEST_RASPBERRYPI_GPIO_INTERRUPT_BOTH_INPUT, InterruptEdge.BOTH, gpio_testcallback)

    gpio.set_pin(TEST_RASPBERRYPI_GPIO_INTERRUPT_BOTH_OUTPUT, True)  # set output high
    time.sleep(0.2)  # wait to callback function happens
    assert interrupt_count == 1  # interrupt on rising edge
    
    gpio.set_pin(TEST_RASPBERRYPI_GPIO_INTERRUPT_BOTH_OUTPUT, False)  # set output low
    time.sleep(0.2)  # wait to callback function happens
    assert interrupt_count == 2  #  interrupt on falling edge
