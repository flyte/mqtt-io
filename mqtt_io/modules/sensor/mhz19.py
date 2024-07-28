"""
MH-Z19 NDIR CO2 sensor
"""

from mqtt_io.modules.sensor import GenericSensor
from mqtt_io.types import CerberusSchemaType, ConfigType, SensorValueType

REQUIREMENTS = ("pyserial",)
CONFIG_SCHEMA: CerberusSchemaType = {
    "device": {"type": 'string', "required": True, "empty": False},
    "range": {"type": 'integer', "required": False, "empty": False, "default": 5000,
                  "allowed": [2000, 5000, 10000]},
}

class Sensor(GenericSensor):
    """
    Implementation of Sensor class for the MH-Z19 CO2 sensor using UART/serial.
    """

    @staticmethod
    def _calc_checksum(data: bytes) -> bytes:
        value = sum(data[1:]) % 0x100
        value = (0xff - value + 1) % 0x100
        return value.to_bytes(1, "big")

    @staticmethod
    def _check_checksum(data: bytes) -> bool:
        return Sensor._calc_checksum(data[:-1]) == data[-1:]

    @staticmethod
    def _add_checksum(data: bytes) -> bytes:
        return data + Sensor._calc_checksum(data)

    def setup_module(self) -> None:
        # pylint: disable=import-error,import-outside-toplevel
        import serial  # type: ignore

        self.ser = serial.Serial(
            port=self.config["device"],
            baudrate=9600,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
        )

        # setup detection range
        cmd = Sensor._add_checksum(b"\xff\x01\x99\x00\x00\x00" +
                                   self.config["range"].to_bytes(2, "big"))
        self.ser.write(cmd)
        # no response

    def cleanup(self) -> None:
        self.ser.close()

    def get_value(self, sens_conf: ConfigType) -> SensorValueType:
        self.ser.write(Sensor._add_checksum(b"\xff\x01\x86\x00\x00\x00\x00\x00"))
        resp = self.ser.read(9)

        if len(resp) == 9:
            if resp[0:2] == b"\xff\x86" and Sensor._check_checksum(resp):
                return int.from_bytes(resp[2:4], "big")

        return None
