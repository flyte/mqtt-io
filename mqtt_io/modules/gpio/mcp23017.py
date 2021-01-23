from __future__ import absolute_import

from . import GenericGPIO, PinDirection, PinPUD

REQUIREMENTS = ("adafruit_circuitpython_mcp230xx",)
CONFIG_SCHEMA = {
    "chip_addr": {"type": "integer", "required": False, "empty": False},
}

DIRECTIONS = None
PULLUPS = None


class GPIO(GenericGPIO):
    """
    Implementation of GPIO class for the MCP23017 IO expander chip.
    """

    def __init__(self, config):
        global DIRECTIONS, PULLUPS
        import board
        import busio
        import digitalio
        from adafruit_mcp230xx import mcp23017

        DIRECTIONS = {
            PinDirection.INPUT: digitalio.Direction.INPUT,
            PinDirection.OUTPUT: digitalio.Direction.OUTPUT,
        }
        # Pulldowns are not supported on MCP23017
        PULLUPS = {
            PinPUD.UP: digitalio.Pull.UP,
            None: None,
        }
        i2c = busio.I2C(board.SCL, board.SDA)

        # Use the "protected" constant for the default address
        self.io = mcp23017.MCP23017(
            i2c, address=config.get("chip_addr", mcp23017._MCP23017_ADDRESS)
        )

    def setup_pin(self, pin, direction, pullup, pin_config):
        mcp_pin = self.io.get_pin(pin)
        # FIXME: Needing refactor or cleanup -@flyte at 26/01/2020, 15:48:43
        # Modules shouldn't know about config. We should have a specific API
        # for setup_pin etc. including 'initial', or using kwargs if necessary.

        # Set to True if 'high', False if 'low'
        initial = pin_config.get("initial", "low") == "high"
        if direction == PinDirection.OUTPUT:
            mcp_pin.switch_to_output(value=initial)
        else:
            mcp_pin.switch_to_input(pull=PULLUPS[pullup])

    def set_pin(self, pin, value):
        self.io.get_pin(pin).value = value

    def get_pin(self, pin):
        return self.io.get_pin(pin).value
