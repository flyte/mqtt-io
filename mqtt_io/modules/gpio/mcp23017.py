from __future__ import absolute_import

from . import GenericGPIO, InterruptEdge, InterruptSupport, PinDirection, PinPUD

REQUIREMENTS = ("adafruit_circuitpython_mcp230xx",)
CONFIG_SCHEMA = {
    "chip_addr": {"type": "integer", "required": False, "empty": False},
}

DIRECTIONS = None
PULLUPS = None


class GPIO(GenericGPIO):
    """
    Implementation of GPIO class for the MCP23017 IO expander chip.

    Pin numbers 0 - 15.
    """

    # | InterruptSupport.CAPTURE_REGISTER
    INTERRUPT_SUPPORT = (
        InterruptSupport.FLAG_REGISTER
        | InterruptSupport.INTERRUPT_PIN
        | InterruptSupport.SET_TRIGGERS
    )

    def setup_module(self):
        global DIRECTIONS, PULLUPS
        import board
        import busio
        import digitalio
        from adafruit_mcp230xx import mcp23017

        i2c = busio.I2C(board.SCL, board.SDA)
        DIRECTIONS = {
            PinDirection.INPUT: digitalio.Direction.INPUT,
            PinDirection.OUTPUT: digitalio.Direction.OUTPUT,
        }
        # Pulldowns are not supported on MCP23017
        PULLUPS = {
            PinPUD.UP: digitalio.Pull.UP,
            None: None,
        }

        # Use the "protected" constant for the default address
        self.io = mcp23017.MCP23017(
            i2c, address=self.config.get("chip_addr", mcp23017._MCP23017_ADDRESS)
        )

    def setup_pin(self, pin, direction, pullup=None, initial="low", **kwargs):
        mcp_pin = self.io.get_pin(pin)

        # Set to True if 'high', False if 'low'
        initial = initial == "high"
        if direction == PinDirection.OUTPUT:
            mcp_pin.switch_to_output(value=initial)
        else:
            mcp_pin.switch_to_input(pull=PULLUPS[pullup])

    def setup_interrupt(self, pin, edge, in_conf):
        if edge == InterruptEdge.BOTH:
            # Set this pin to interrupt when it changes from its previous value
            self.io.interrupt_configuration &= ~(1 << pin)
        else:
            # Enable comparison to default value for this pin
            self.io.interrupt_configuration |= 1 << pin

        if edge == InterruptEdge.RISING:
            # Set default value for this pin to be 0
            self.io.default_value &= ~(1 << pin)
        elif edge == InterruptEdge.FALLING:
            # Set default value for this pin to be 1
            self.io.default_value |= 1 << pin

        # Enable the interrupt on this pin
        self.io.interrupt_enable |= 1 << pin

    def set_pin(self, pin, value):
        self.io.get_pin(pin).value = value

    def get_pin(self, pin):
        return self.io.get_pin(pin).value

    def get_int_pins(self):
        return self.io.int_flag
