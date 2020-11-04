from __future__ import absolute_import
import time, sys
from pi_mqtt_gpio.modules import GenericGPIO, PinDirection, PinPullup


REQUIREMENTS = ("smbus",)
CONFIG_SCHEMA = {
    "i2c_bus_num": {"type": "integer", "required": True, "empty": False},
    "chip_addr": {"type": "integer", "required": True, "empty": False},
}

PULLUPS = None


class GPIO(GenericGPIO):
    """
    Implementation of GPIO class for the PCF8574 IO expander chip.
    """

    def __init__(self, config):
        global PULLUPS
        PULLUPS = {
            PinPullup.UP: "enable",
            PinPullup.DOWN: "disable",
            PinPullup.OFF: "disable",
        }

        self.io = MCP230XX(
            "MCP23017", config["i2c_bus_num"], config["chip_addr"], "16bit"
        )

    def setup_pin(self, pin, direction, pullup, pin_config):
        if direction == PinDirection.INPUT:
            self.io.set_mode(pin, "input", PULLUPS[pullup])
        else:
            self.io.set_mode(pin, "output")

        initial = pin_config.get("initial")
        if initial is not None:
            if initial == "high":
                self.set_pin(pin, True)
            elif initial == "low":
                self.set_pin(pin, False)

    def set_pin(self, pin, value):
        self.io.output(pin, value)

    def get_pin(self, pin):
        return self.io.input(pin)


"""MCP230XX, python module for the MCP230008 and MCP230017 GPIO
expander chips

created September 9, 2017
last modified October 8, 2017"""

"""
Copyright 2017 Owain Martin

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""


class MCP230XX:
    def __init__(self, chip, smbus, i2cAddress, regScheme="16bit"):

        self.chip = chip
        self.bus = smbus
        self.i2cAddress = i2cAddress

        if self.chip == "MCP23008":
            self.bank = "8bit"
        else:
            self.bank = regScheme

        self.callBackFuncts = []
        for i in range(0, 17):
            self.callBackFuncts.append(["empty", "emtpy"])

        return

    def single_access_read(self, reg=0x00):
        """single_access_read, function to read a single data register
        of the MCP230xx gpio expander"""

        dataTransfer = self.bus.read_byte_data(self.i2cAddress, reg)

        return dataTransfer

    def single_access_write(self, reg=0x00, regValue=0x0):
        """single_access_write, function to write to a single data register
        of the MCP230xx gpio expander"""

        self.bus.write_byte_data(self.i2cAddress, reg, regValue)

        return

    def register_bit_select(self, pin, reg8A, reg16A, reg8B, reg16B):
        """register_bit_select,  function to return the proper
        register and bit position to use for a particular GPIO
        and GPIO function"""

        # need to add way of throwing an error if pin is outside
        # of 0-15 range

        if pin >= 0 and pin < 8:
            bit = pin
            if self.bank == "16bit":
                reg = reg16A
            else:  # self.bank = '8bit'
                reg = reg8A
        elif pin >= 8 and pin < 16:
            bit = pin - 8
            if self.bank == "16bit":
                reg = reg16B
            else:  # self.bank = '8bit'
                reg = reg8B

        return reg, bit

    def interrupt_options(self, outputType="activehigh", bankControl="separate"):
        """interrupt_options, function to set the options for the 2 interrupt
        pins"""

        if self.bank == "16bit":
            reg = 0x0A
        else:  # self.bank = '8bit'
            reg = 0x05

        if outputType == "activelow":
            odrBit = 0
            intpolBit = 0
        elif outputType == "opendrain":
            odrBit = 1
            intpolBit = 0
        else:  # outputType = 'activehigh'
            odrBit = 0
            intpolBit = 1

        if bankControl == "both":
            mirrorBit = 1
        else:  # bankControl = 'separate'
            mirrorBit = 0

        regValue = self.single_access_read(reg)
        regValue = regValue & 0b10111001
        regValue = regValue | (mirrorBit << 6) + (odrBit << 2) + (intpolBit << 1)
        self.single_access_write(reg, regValue)

        return

    def set_register_addressing(self, regScheme="8bit"):
        """set_register_addressing, function to change how the registers
        are mapped.  For an MCP23008, bank should always equal '8bit'.  This
        sets bit 7 of the IOCON register"""

        if self.bank == "16bit":
            reg = 0x0A
        else:  # self.bank = '8bit'
            reg = 0x05

        if regScheme == "16bit":
            bankBit = 0
            self.bank = "16bit"
        else:  # regScheme = '8bit'
            bankBit = 1
            self.bank = "8bit"

        regValue = self.single_access_read(reg)
        regValue = regValue & 0b01111111
        regValue = regValue | (bankBit << 7)
        self.single_access_write(reg, regValue)

        return

    def set_mode(self, pin, mode, pullUp="disable"):
        """set_mode, function to set up a GPIO pin to either an input
        or output. The input pullup resistor can also be enabled.
        This sets the appropriate bits in the IODIRA/B and GPPUA/B
        registers"""

        # GPIO direction set up section

        reg, bit = self.register_bit_select(
            pin, reg8A=0x00, reg16A=0x00, reg8B=0x10, reg16B=0x01
        )

        regValue = self.single_access_read(reg)

        if mode == "output":
            mask = 0b11111111 & ~(1 << bit)
            regValue = regValue & mask
            self.single_access_write(reg, regValue)

        else:  # mode = input
            mask = 0x00 | (1 << bit)
            regValue = regValue | mask
            self.single_access_write(reg, regValue)

        # pullUp enable/disable section

        if mode == "input":
            reg, bit = self.register_bit_select(
                pin, reg8A=0x06, reg16A=0x0C, reg8B=0x16, reg16B=0x0D
            )

            regValue = self.single_access_read(reg)

            if pullUp == "enable":
                mask = 0x00 | (1 << bit)
                regValue = regValue | mask
                self.single_access_write(reg, regValue)
            else:  # pullUp = disable
                mask = 0b11111111 & ~(1 << bit)
                regValue = regValue & mask
                self.single_access_write(reg, regValue)

        return

    def invert_input(self, pin, invert=False):
        """invert_input, function to invert the output of the pins
        corresponding GPIO register bit.  Sets bit in IPOLA/B"""

        # input invert on/off section

        reg, bit = self.register_bit_select(
            pin, reg8A=0x01, reg16A=0x02, reg8B=0x11, reg16B=0x03
        )

        regValue = self.single_access_read(reg)

        if invert == True:
            mask = 0x00 | (1 << bit)
            regValue = regValue | mask
            self.single_access_write(reg, regValue)
        else:  # invert = False
            mask = 0b11111111 & ~(1 << bit)
            regValue = regValue & mask
            self.single_access_write(reg, regValue)

        return

    def output(self, pin, value):
        """output, function to set the state of a GPIO output
        pin via the appropriate bit in the OLATA/B registers"""

        reg, bit = self.register_bit_select(
            pin, reg8A=0x0A, reg16A=0x14, reg8B=0x1A, reg16B=0x15
        )

        regValue = self.single_access_read(reg)

        if value == 1:
            # set output high
            mask = 0x00 | (1 << bit)
            regValue = regValue | mask
        else:
            # set output low
            mask = 0b11111111 & ~(1 << bit)
            regValue = regValue & mask

        self.single_access_write(reg, regValue)

        return

    def input(self, pin):
        """input, function to get the current level of a GPIO input
        pin by reading the appropriate bit in the GPIOA/B registers"""

        reg, bit = self.register_bit_select(
            pin, reg8A=0x09, reg16A=0x12, reg8B=0x19, reg16B=0x13
        )

        regValue = self.single_access_read(reg)

        mask = 0x00 | (1 << bit)
        value = regValue & mask
        value = value >> bit

        return value

    def input_at_interrupt(self, pin):
        """input_at_interrupt, function to get the current level of a GPIO input
        pin when an interrupt has occurred by reading the appropriate bit in the
        INTCAPA/B registers"""

        reg, bit = self.register_bit_select(
            pin, reg8A=0x08, reg16A=0x10, reg8B=0x18, reg16B=0x11
        )

        regValue = self.single_access_read(reg)

        mask = 0x00 | (1 << bit)
        value = regValue & mask
        value = value >> bit

        return value

    def add_interrupt(self, pin, callbackFunctLow="empty", callbackFunctHigh="empty"):
        """add_interrupt, function to set up the interrupt options
        for a specific GPIO including callback functions to be executed
        when an interrupt occurs"""

        # set bit in GPINTENA/B registers

        reg, bit = self.register_bit_select(
            pin, reg8A=0x02, reg16A=0x04, reg8B=0x12, reg16B=0x05
        )

        regValue = self.single_access_read(reg)
        mask = 0x00 | (1 << bit)
        regValue = regValue | mask
        self.single_access_write(reg, regValue)

        # set bit in INTCONA/B registers

        reg, bit = self.register_bit_select(
            pin, reg8A=0x04, reg16A=0x08, reg8B=0x14, reg16B=0x09
        )

        regValue = self.single_access_read(reg)
        mask = 0b11111111 & ~(1 << bit)
        regValue = regValue & mask
        self.single_access_write(reg, regValue)

        # set bit in DEFVALA/B registers - not required

        # set call back functions in function list
        self.callBackFuncts[pin][0] = callbackFunctLow
        self.callBackFuncts[pin][1] = callbackFunctHigh

        return

    def remove_interrupt(self, pin):
        """remove_interrupt, function to remove the interrupt settings
        from an MCP230xx pin"""

        # set bit in GPINTENA/B registers

        reg, bit = self.register_bit_select(
            pin, reg8A=0x02, reg16A=0x04, reg8B=0x12, reg16B=0x05
        )

        regValue = self.single_access_read(reg)
        mask = 0b11111111 & ~(1 << bit)
        regValue = regValue & mask
        self.single_access_write(reg, regValue)

        # reset call back functions in function list to 'empty'
        self.callBackFuncts[pin][0] = "empty"
        self.callBackFuncts[pin][1] = "empty"

        return

    def callbackA(self, gpio):
        """function called by RPI.GPIO on an bank A interrupt condition.
        This function will figure out which MCP230xx pin caused the
        interrupt and initiate the appropriate callback function"""

        # read INTF register

        if self.bank == "16bit":
            reg = 0x0E
        else:  # self.bank = '8bit'
            reg = 0x07

        regValue = self.single_access_read(reg)

        pin = -1

        for i in range(0, 8):
            if regValue == (1 << i):
                pin = i
                break

        value = self.input_at_interrupt(pin)

        if self.callBackFuncts[pin][value] != "empty":
            self.callBackFuncts[pin][value](pin)

        return

    def callbackB(self, gpio):
        """function called by RPI.GPIO on an bank B interrupt condition.
        This function will figure out which MCP230xx pin caused the
        interrupt and initiate the appropriate callback function"""

        # read INTF register

        if self.bank == "16bit":
            reg = 0x0F
        else:  # self.bank = '8bit'
            reg = 0x17

        regValue = self.single_access_read(reg)

        pin = -1

        for i in range(0, 8):
            if regValue == (1 << i):
                pin = i + 8
                break

        value = self.input_at_interrupt(pin)

        if self.callBackFuncts[pin][value] != "empty":
            self.callBackFuncts[pin][value](pin)

        return

    def callbackBoth(self, gpio):
        """function called by RPI.GPIO on either a bank A  or bank B
        interrupt condition. This function will figure out which MCP230xx
        pin caused the interrupt and initiate the appropriate callback function"""

        # read INTF register

        if self.bank == "16bit":
            regA = 0x0E
            regB = 0x0F
        else:  # self.bank = '8bit'
            regA = 0x07
            regB = 0x17

        regValue = self.single_access_read(regA)

        pin = -1

        # check GPIOA bank for interrupt

        for i in range(0, 8):
            if regValue == (1 << i):
                pin = i
                break

        # check GPIOB bank for interrupt if none found in GPIOA bank

        if pin == -1:
            regValue = self.single_access_read(regB)
            for i in range(0, 8):
                if regValue == (1 << i):
                    pin = i + 8
                    break

        value = self.input_at_interrupt(pin)

        if self.callBackFuncts[pin][value] != "empty":
            self.callBackFuncts[pin][value](pin)

        return

    def register_reset(self):
        """register_reset, function to put chip back to default
        settings"""

        # print('resetting')

        if self.chip == "MCP23008":
            self.single_access_write(0x00, 0xFF)
            for i in range(1, 12):
                self.single_access_write(i, 0x00)
        else:
            self.set_register_addressing("16bit")
            self.single_access_write(0x00, 0xFF)
            self.single_access_write(0x01, 0xFF)
            for i in range(2, 22):
                self.single_access_write(i, 0x00)

        return

    def __del__(self):
        """__del__, function to clean up expander object and put chip
        back to default settings"""

        # print('deleting')

        self.register_reset()

        return
