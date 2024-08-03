# -*- coding:utf-8 -*-

"""
  Adapted from the below by @linucks

  @file DFRobot_RaspberryPi_Expansion_Board.py
  @brief This RaspberryPi expansion board can communicate with RaspberryPi via I2C. It has 10 GPIOs, 1 SPI, 4 I2Cs and 1 uart.
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

_PWM_CHAN_COUNT = 4
_ADC_CHAN_COUNT = 4

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

    """ last operate status, users can use this variable to determine the result of a function call. """
    last_operate_status = STA_OK

    """ Global variables """
    ALL = 0xFFFFFFFF

    @abc.abstractmethod
    def _write_bytes(self, reg, buf):
        pass

    @abc.abstractmethod
    def _read_bytes(self, reg, length):
        pass

    def __init__(self, addr):
        self._addr = addr
        self._is_pwm_enable = False

    def begin(self):
        """
        @brief    Board begin
        @return   Board status
        """
        pid = self._read_bytes(self._REG_PID, 1)
        vid = self._read_bytes(self._REG_VID, 1)
        if self.last_operate_status == self.STA_OK:
            if pid[0] != self._REG_DEF_PID:
                self.last_operate_status = self.STA_ERR_DEVICE_NOT_DETECTED
            elif vid[0] != self._REG_DEF_VID:
                self.last_operate_status = self.STA_ERR_SOFT_VERSION
            else:
                self.set_pwm_disable()
                self.set_pwm_duty(self.ALL, 0)
                self.set_adc_disable()
        return self.last_operate_status

    def set_addr(self, addr):
        """
        @brief    Set board controler address, reboot module to make it effective
        @param address: int    Address to set, range in 1 to 127
        """
        if addr < 1 or addr > 127:
            self.last_operate_status = self.STA_ERR_PARAMETER
            return
        self._write_bytes(self._REG_SLAVE_ADDR, [addr])

    def _parse_id(self, limit, id_):
        ld = []
        if isinstance(id_, list) is False:
            id_ = id_ + 1
            ld.append(id_)
        else:
            ld = [i + 1 for i in id_]
        if ld == self.ALL:
            return range(1, limit + 1)
        for i in ld:
            if i < 1 or i > limit:
                self.last_operate_status = self.STA_ERR_PARAMETER
                return []
        return ld

    def set_pwm_enable(self):
        """
        @brief    Set pwm enable, pwm channel need external power
        """
        self._write_bytes(self._REG_PWM_CONTROL, [0x01])
        if self.last_operate_status == self.STA_OK:
            self._is_pwm_enable = True
        time.sleep(0.01)

    def set_pwm_disable(self):
        """
        @brief    Set pwm disable
        """
        self._write_bytes(self._REG_PWM_CONTROL, [0x00])
        if self.last_operate_status == self.STA_OK:
            self._is_pwm_enable = False
        time.sleep(0.01)

    def set_pwm_frequency(self, freq):
        """
        @brief    Set pwm frequency
        @param freq: int    Frequency to set, in range 1 - 1000
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

    def set_pwm_duty(self, chan, duty):
        """
        @brief    Set selected channel duty
        @param chan: list     One or more channels to set, items in range 1 to 4, or chan = self.ALL
        @param duty: float    Duty to set, in range 0.0 to 100.0
        """
        if duty < 0 or duty > 100:
            self.last_operate_status = self.STA_ERR_PARAMETER
            return
        for i in self._parse_id(_PWM_CHAN_COUNT, chan):
            self._write_bytes(
                self._REG_PWM_DUTY1 + (i - 1) * 2, [int(duty), int((duty * 10) % 10)]
            )

    def set_adc_enable(self):
        """
        @brief    Set adc enable
        """
        self._write_bytes(self._REG_ADC_CTRL, [0x01])

    def set_adc_disable(self):
        """
        @brief    Set adc disable
        """
        self._write_bytes(self._REG_ADC_CTRL, [0x00])

    def get_adc_value(self, chan):
        """
        @brief    Get adc value
        @param chan: int    Channel to get, in range 1 to 4, or self.ALL
        @return :list       List of value
        """
        for i in self._parse_id(_ADC_CHAN_COUNT, chan):
            rslt = self._read_bytes(self._REG_ADC_VAL1 + (i - 1) * 2, 2)
        return (rslt[0] << 8) | rslt[1]

    def detecte(self):
        """
        @brief    If you forget address you had set, use this to detecte them, must have class instance
        @return   Board list conformed
        """
        l = []
        back = self._addr
        for i in range(1, 127):
            self._addr = i
            if self.begin() == self.STA_OK:
                l.append(i)
        l = map(hex, l)
        self._addr = back
        self.last_operate_status = self.STA_OK
        return l


class DFRobotExpansionBoardDigitalRGBLED:
    """Class for digital RGB LED control."""

    def __init__(self, board):
        """
        @param board: DFRobot_Expansion_Board   Board instance to operate digital rgb led, test LED: https://www.dfrobot.com/product-1829.html
                                                Warning: LED must connect to pwm channel, otherwise may destory Pi IO
        """
        self._board = board
        self._chan_r = 0
        self._chan_g = 0
        self._chan_b = 0

    def begin(self, chan_r, chan_g, chan_b):
        """
        @brief    Set digital rgb led color channel, these parameters not repeat
        @param chan_r: int    Set color red channel id, in range 1 to 4
        @param chan_g: int    Set color green channel id, in range 1 to 4
        @param chan_b: int    Set color blue channel id, in range 1 to 4
        """
        if chan_r == chan_g or chan_r == chan_b or chan_g == chan_b:
            return
        if (
            chan_r < _PWM_CHAN_COUNT
            and chan_g < _PWM_CHAN_COUNT
            and chan_b < _PWM_CHAN_COUNT
        ):
            self._chan_r = chan_r
            self._chan_g = chan_g
            self._chan_b = chan_b
            self._board.set_pwm_enable()
            self._board.set_pwm_frequency(1000)
            self._board.set_pwm_duty(self._board.ALL, 100)

    def color888(self, r, g, b):
        """
        @brief    Set LED to true-color
        @param r: int   Color components red
        @param g: int   Color components green
        @param b: int   Color components blue
        """
        self._board.set_pwm_duty([self._chan_r], 100 - (r & 0xFF) * 100 // 255)
        self._board.set_pwm_duty([self._chan_g], 100 - (g & 0xFF) * 100 // 255)
        self._board.set_pwm_duty([self._chan_b], 100 - (b & 0xFF) * 100 // 255)

    def color24(self, color):
        """
        @brief    Set LED to 24-bits color
        @param color: int   24-bits color
        """
        color &= 0xFFFFFF
        self.color888(color >> 16, (color >> 8) & 0xFF, color & 0xFF)

    def color565(self, color):
        """
        @brief    Set LED to 16-bits color
        @param color: int   16-bits color
        """
        color &= 0xFFFF
        self.color888((color & 0xF800) >> 8, (color & 0x7E0) >> 3, (color & 0x1F) << 3)


class DFRobotExpansionBoardServo:
    """Class to operate a servo"""

    def __init__(self, board):
        """
        @param board: DFRobot_Expansion_Board   Board instance to operate servo, test servo: https://www.dfrobot.com/product-255.html
                                                Warning: servo must connect to pwm channel, otherwise may destory Pi IO
        """
        self._board = board

    def begin(self):
        """
        @brief    Board servo begin
        """
        self._board.set_pwm_enable()
        self._board.set_pwm_frequency(50)
        self._board.set_pwm_duty(self._board.ALL, 0)

    def move(self, id_, angle):
        """
        @brief    Servos move
        @param id_: list     One or more servos to set, items in range 1 to 4, or chan = self.ALL
        @param angle: int   Angle to move, in range 0 to 180
        """
        if 0 <= angle <= 180:
            self._board.set_pwm_duty(id_, (0.5 + (float(angle) / 90.0)) / 20 * 100)


class DFRobotExpansionBoardIIC(DFRobotExpansionBoard):
    """Class for IIC communication with Expansion Board."""

    def __init__(self, bus_id, addr):
        """
        @param bus_id: int   Which bus to operate
        @oaram addr: int     Board controler address
        """
        # pylint: disable=import-outside-toplevel,import-error
        import smbus

        self._bus = smbus.SMBus(bus_id)
        super().__init__(addr)

    def _write_bytes(self, reg, buf):
        # pylint: disable=broad-exception-caught
        self.last_operate_status = self.STA_ERR_DEVICE_NOT_DETECTED
        try:
            self._bus.write_i2c_block_data(self._addr, reg, buf)
            self.last_operate_status = self.STA_OK
        except Exception:
            _LOG.warning("DFRobotExpansionBoardIIC I2C write error")

    def _read_bytes(self, reg, length):
        # pylint: disable=broad-exception-caught
        self.last_operate_status = self.STA_ERR_DEVICE_NOT_DETECTED
        try:
            rslt = self._bus.read_i2c_block_data(self._addr, reg, length)
            self.last_operate_status = self.STA_OK
            return rslt
        except Exception:
            _LOG.warning("DFRobotExpansionBoardIIC I2C read error")
            return [0] * length
