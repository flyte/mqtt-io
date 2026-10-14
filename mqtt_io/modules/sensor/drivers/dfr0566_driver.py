# -*- coding:utf-8 -*-

"""
  Adapted from the below by @linucks

  @file DFRobot_RaspberryPi_Expansion_Board.py
  @brief This RaspberryPi expansion board can communicate with RaspberryPi via I2C.
         It has 10 GPIOs, 1 SPI, 4 I2Cs and 1 uart.
  @copyright   Copyright (c) 2010 DFRobot Co.Ltd (http://www.dfrobot.com)
  @license     The MIT License (MIT)
  @author      Frank(jiehan.guo@dfrobot.com)
  @version     V1.0
  @date        2019-3-28
  @url https://github.com/DFRobot/DFRobot_RaspberryPi_Expansion_Board
"""
import abc
import logging
import time
from typing import List

BOARD_SETUP_TRIES = 3
BOARD_SETUP_TIMEOUT = 2
PMW_CHANNELS = 4

_LOG = logging.getLogger(__name__)


class DFRobotExpansionBoard(abc.ABC):
    """Base class for Expansion Board functionality."""

    _REG_SLAVE_ADDR = 0x00
    _REG_PID = 0x01
    _REG_VID = 0x02
    _REG_PWM_CONTROL = 0x03
    _REG_PWM_FREQ = 0x04
    _REG_PWM_DUTY1 = 0x06
    _REG_PWM_DUTY2 = 0x08
    _REG_PWM_DUTY3 = 0x0A
    _REG_PWM_DUTY4 = 0x0C
    _REG_ADC_CTRL = 0x0E
    _REG_ADC_VAL1 = 0x0F
    _REG_ADC_VAL2 = 0x11
    _REG_ADC_VAL3 = 0x13
    _REG_ADC_VAL4 = 0x15

    _REG_DEF_PID = 0xDF
    _REG_DEF_VID = 0x10

    """ Enum board Analog channels """
    A0 = 0x00
    A1 = 0x01
    A2 = 0x02
    A3 = 0x03

    """ Board status """
    STA_OK = 0x00
    STA_ERR = 0x01
    STA_ERR_DEVICE_NOT_DETECTED = 0x02
    STA_ERR_SOFT_VERSION = 0x03
    STA_ERR_PARAMETER = 0x04

    """Last operation status: use this variable to determine the result of a function call. """
    last_operate_status = STA_OK

    @abc.abstractmethod
    def _write_bytes(self, reg: int, buf: List[int]) -> None:
        pass

    @abc.abstractmethod
    def _read_bytes(self, reg: int, length: int) -> List[int]:
        pass

    def __init__(self, addr: int) -> None:
        self._addr = addr
        self._is_pwm_enable = False

    def begin(self, disable_pmw: bool = False, disable_adc: bool = False) -> int:
        """
        Board begin
        return:   Board status
        """
        pid = self._read_bytes(self._REG_PID, 1)
        vid = self._read_bytes(self._REG_VID, 1)
        if self.last_operate_status == self.STA_OK:
            if pid[0] != self._REG_DEF_PID:
                self.last_operate_status = self.STA_ERR_DEVICE_NOT_DETECTED
            elif vid[0] != self._REG_DEF_VID:
                self.last_operate_status = self.STA_ERR_SOFT_VERSION
            else:
                if disable_pmw:
                    self.set_pwm_disable()
                if disable_adc:
                    self.set_adc_disable()
        return self.last_operate_status

    def set_addr(self, addr: int) -> None:
        """
        Set board controler address, reboot module to make it effective
        addr: int    Address to set, range in 1 to 127
        """
        if addr < 1 or addr > 127:
            self.last_operate_status = self.STA_ERR_PARAMETER
            return
        self._write_bytes(self._REG_SLAVE_ADDR, [addr])

    def setup(self) -> None:
        """Run the board setup."""
        count = 0
        while self.begin() != self.STA_OK:
            count += 1
            if count > BOARD_SETUP_TRIES:
                raise RuntimeError(
                    "Failed to initialise board: %s" % board_status_str(self)
                )
            time.sleep(BOARD_SETUP_TIMEOUT)

    def set_adc_enable(self) -> None:
        """
        Enable the ADC
        """
        self._write_bytes(self._REG_ADC_CTRL, [0x01])

    def set_adc_disable(self) -> None:
        """
        Disable the ADC
        """
        self._write_bytes(self._REG_ADC_CTRL, [0x00])

    def get_adc_value(self, chan: int) -> float:
        """
        Return the ADC value for the given channel.
        """
        rslt = self._read_bytes(self._REG_ADC_VAL1 + chan * 2, 2)
        return (rslt[0] << 8) | rslt[1]

    def set_pwm_enable(self) -> None:
        """
        Set pwm enable, pwm channel need external power
        """
        self._write_bytes(self._REG_PWM_CONTROL, [0x01])
        if self.last_operate_status == self.STA_OK:
            self._is_pwm_enable = True
        time.sleep(0.01)

    def set_pwm_disable(self) -> None:
        """
        Disable the PWM
        """
        self._write_bytes(self._REG_PWM_CONTROL, [0x00])
        if self.last_operate_status == self.STA_OK:
            self._is_pwm_enable = False
        time.sleep(0.01)

    def set_pwm_frequency(self, freq: int) -> None:
        """
        Set PWM frequency:
        freq: int    Frequency to set, in range 1 - 1000
        """
        if freq < 1 or freq > 1000:
            self.last_operate_status = self.STA_ERR_PARAMETER
            return
        is_pwm_enable = self._is_pwm_enable
        self.set_pwm_disable()
        self._write_bytes(self._REG_PWM_FREQ, [freq >> 8, freq & 0xFF])
        time.sleep(0.01)
        if is_pwm_enable:
            self.set_pwm_enable()

    def set_pwm_duty(self, chan: int, duty: float) -> None:
        """
        Set selected channel duty:
        chan: Channel to set, in range 0 - 3
        duty: Duty to set, in range 0.0 to 100.0
        """
        if duty < 0 or duty > 100:
            self.last_operate_status = self.STA_ERR_PARAMETER
            return
        self._write_bytes(
            self._REG_PWM_DUTY1 + chan * 2, [int(duty), int((duty * 10) % 10)]
        )


class DFRobotExpansionBoardIIC(DFRobotExpansionBoard):
    """Class for IIC communication with Expansion Board."""

    def __init__(self, bus_id: int, addr: int) -> None:
        """
        @param bus_id: int   Which bus to operate
        @oaram addr: int     Board controler address
        """
        # pylint: disable=import-outside-toplevel,import-error
        import smbus  # type: ignore

        self._bus = smbus.SMBus(bus_id)
        super().__init__(addr)

    def _write_bytes(self, reg: int, buf: List[int]) -> None:
        self.last_operate_status = self.STA_ERR_DEVICE_NOT_DETECTED
        try:
            self._bus.write_i2c_block_data(self._addr, reg, buf)
            self.last_operate_status = self.STA_OK
        except Exception:  # pylint: disable=broad-except
            _LOG.warning("DFRobotExpansionBoardIIC I2C write error")

    def _read_bytes(self, reg: int, length: int) -> List[int]:
        self.last_operate_status = self.STA_ERR_DEVICE_NOT_DETECTED
        try:
            rslt: List[int] = self._bus.read_i2c_block_data(self._addr, reg, length)
            self.last_operate_status = self.STA_OK
            return rslt
        except Exception:  # pylint: disable=broad-except
            _LOG.warning("DFRobotExpansionBoardIIC I2C read error")
            return [0] * length


class DFRobotExpansionBoardServo:
    """
    board: DFRobot_Expansion_Board
           Board instance to operate servo, test servo: https://www.dfrobot.com/product-255.html

    Warning: servo must connect to pwm channel, otherwise may destory Pi IO
    """

    def __init__(self, board: DFRobotExpansionBoard) -> None:
        """Set the board instance."""
        self._board = board

    def begin(self) -> None:
        """
        Board servo begin
        """
        self._board.set_pwm_enable()
        self._board.set_pwm_frequency(50)
        for channel in range(PMW_CHANNELS):
            self._board.set_pwm_duty(channel, 0)

    def move(self, channel_id: int, angle: int) -> None:
        """
        Move the servo to the given angle.
        channel_id: int    Servos to set in range 0 to 3
        angle: int   Angle to move, in range 0 to 180
        """
        if 0 <= angle <= 180:
            self._board.set_pwm_duty(
                channel_id, (0.5 + (float(angle) / 90.0)) / 20 * 100
            )


def board_status_str(board: DFRobotExpansionBoard) -> str:
    """Return board status as string."""
    return {
        board.STA_OK: "STA_OK",
        board.STA_ERR: "STA_ERR",
        board.STA_ERR_DEVICE_NOT_DETECTED: "STA_ERR_DEVICE_NOT_DETECTED",
        board.STA_ERR_PARAMETER: "STA_ERR_PARAMETER",
        board.STA_ERR_SOFT_VERSION: "STA_ERR_SOFT_VERSION",
    }.get(board.last_operate_status, "unknown error")
