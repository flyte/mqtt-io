from __future__ import absolute_import

import logging
from typing import Any, Dict, List, Optional, cast

from ...exceptions import ConfigValidationFailed
from ...types import ConfigType, PinType
from . import GenericGPIO, InterruptEdge, InterruptSupport, PinDirection, PinPUD

_LOG = logging.getLogger(__name__)

REQUIREMENTS = ("adafruit_circuitpython_mcp230xx",)
CONFIG_SCHEMA = {
    "chip_addr": {"type": "integer", "required": False, "empty": False},
}

DIRECTIONS: Dict[PinDirection, Any] = {}
PULLUPS: Dict[PinPUD, Any] = {}


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

    def setup_module(self) -> None:
        # pylint: disable=global-statement,import-outside-toplevel
        global DIRECTIONS, PULLUPS
        import board  # type: ignore
        import busio  # type: ignore
        import digitalio  # type: ignore
        from adafruit_mcp230xx import mcp23017  # type: ignore

        i2c = busio.I2C(board.SCL, board.SDA)
        DIRECTIONS = {
            PinDirection.INPUT: digitalio.Direction.INPUT,
            PinDirection.OUTPUT: digitalio.Direction.OUTPUT,
        }
        # Pulldowns are not supported on MCP23017
        PULLUPS = {
            PinPUD.UP: digitalio.Pull.UP,
            PinPUD.OFF: None,
        }

        # Use the "protected" constant for the default address
        self.io = mcp23017.MCP23017(
            i2c, address=self.config.get("chip_addr", mcp23017._MCP23017_ADDRESS)
        )
        self.io.clear_ints()

    def setup_pin(
        self,
        pin: PinType,
        direction: PinDirection,
        pullup: PinPUD,
        pin_config: ConfigType,
        initial: Optional[str] = None,
    ) -> None:
        if not isinstance(pin, int):
            raise ConfigValidationFailed("MCP23017 pins must be integers")
        mcp_pin = self.io.get_pin(pin)
        mcp_pin.direction = DIRECTIONS[direction]
        if direction == PinDirection.OUTPUT:
            if initial is not None:
                mcp_pin.value = initial == "high"
        else:
            mcp_pin.pull = PULLUPS[pullup]

    def setup_interrupt(
        self, pin: PinType, edge: InterruptEdge, in_conf: ConfigType
    ) -> None:
        # TODO: Tasks pending completion -@flyte at 29/01/2021, 19:14:16
        # Make this a wrapper task on GenericGPIO
        self.interrupt_edges[pin] = edge

        # TODO: Tasks pending completion -@flyte at 29/01/2021, 19:42:23
        # Add ODR and INTPOL values of the IOCON register to the config for this module
        _LOG.debug(
            "MCP23017 module %s IOCON: %s", self.config["name"], bin(self.io.io_control)
        )

        pin = cast(int, pin)

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

    def set_pin(self, pin: PinType, value: bool) -> None:
        self.io.get_pin(pin).value = value

    def get_pin(self, pin: PinType) -> bool:
        return bool(self.io.get_pin(pin).value)

    def get_int_pins(self) -> List[PinType]:
        return cast(List[PinType], self.io.int_flag)
