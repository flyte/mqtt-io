"""
PN532 NFC/RFID reader
"""

# `device` value should be set according to nfcpy manual:
#  https://nfcpy.readthedocs.io/en/latest/topics/get-started.html#open-a-local-device
# `tty` - tries all serial ports and drivers and uses first one
# `tty:S0:pn532` - uses pn532 reader on /dev/ttyS0
# `ttyUSB0` - can be used when pn532 is connected via USB UART module
# `usb` - opens first compatible usb reader
#
# List of supported devices: https://nfcpy.readthedocs.io/en/latest/overview.html#supported-devices

from typing import Optional
from mqtt_io.types import ConfigType
from . import GenericStream

REQUIREMENTS = ("nfcpy",)
CONFIG_SCHEMA = {
    "device": {"type": "string", "required": True, "empty": False, "default": "tty"},
}

class Stream(GenericStream):
    """
    Implementation of stream module for reading PM532 tags via UART
    """

    def __init__(self, config: ConfigType):
        self.last_seen_tag = None
        super().__init__(config)

    def setup_module(self) -> None:
        # pylint: disable=import-outside-toplevel,import-error,attribute-defined-outside-init,import
        from nfc import ContactlessFrontend
        self.clf = ContactlessFrontend(self.config["device"])

    def read(self) -> Optional[bytes]:
        # pylint: disable=import-outside-toplevel,import-error,attribute-defined-outside-init
        from binascii import hexlify
        self.clf.connect(rdwr={'on-connect': self.__connected})
        return hexlify(self.last_seen_tag.identifier)

    def write(self, data: bytes) -> None:
        pass

    def cleanup(self) -> None:
        self.clf.close()

    def __connected(self, tag) -> bool:
        self.last_seen_tag = tag
        return False
