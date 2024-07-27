"""
Serial port
"""

from typing import Optional

from . import GenericStream

REQUIREMENTS = ("pyserial",)

BYTESIZE_CHOICES = (5, 6, 7, 8)
PARITY_CHOICES = ("none", "odd", "even", "mark", "space")
STOPBITS_CHOICES = (1, 1.5, 2)

CONFIG_SCHEMA = {
    "device": {"type": "string", "required": True, "empty": False},
    "baud": {"type": "integer", "required": True, "empty": False},
    "timeout": {"type": "integer", "required": False, "empty": False, "default": 20},
    "bytesize": {
        "type": "integer",
        "required": False,
        "default": 8,
        "empty": False,
        "allowed": BYTESIZE_CHOICES,
    },
    "parity": {
        "type": "string",
        "required": False,
        "default": "none",
        "empty": False,
        "allowed": PARITY_CHOICES,
    },
    "stopbits": {
        "type": "float",
        "required": False,
        "default": 1,
        "empty": False,
        "allowed": STOPBITS_CHOICES,
    },
}

# pylint: disable=no-member

# IDEA: Possible implementations -@flyte at 04/03/2021, 18:32:05
# Use the asyncio event loop to fire a callback when data is available on the serial port?


class Stream(GenericStream):
    """
    Stream module for sending to and receiving from serial ports.
    """

    def setup_module(self) -> None:
        # pylint: disable=import-error,import-outside-toplevel
        import serial  # type: ignore

        self.ser = serial.Serial(
            port=self.config["device"],
            baudrate=self.config["baud"],
            timeout=self.config["timeout"],
            bytesize={
                5: serial.FIVEBITS,
                6: serial.SIXBITS,
                7: serial.SEVENBITS,
                8: serial.EIGHTBITS,
            }[self.config["bytesize"]],
            parity= {
                "none": serial.PARITY_NONE,
                "odd": serial.PARITY_ODD,
                "even": serial.PARITY_EVEN,
                "mark": serial.PARITY_MARK,
                "space": serial.PARITY_SPACE,
            }[self.config["parity"]],
            stopbits={
                1: serial.STOPBITS_ONE,
                1.5: serial.STOPBITS_ONE_POINT_FIVE,
                2: serial.STOPBITS_TWO,
            }[self.config["stopbits"]],
        )
        self.ser.flushInput()

    def read(self) -> Optional[bytes]:
        return self.ser.read(self.ser.in_waiting) or None

    def write(self, data: bytes) -> None:
        self.ser.write(data)

    def cleanup(self) -> None:
        self.ser.close()
