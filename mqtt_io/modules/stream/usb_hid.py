"""
USB HID
"""

from typing import Optional

from . import GenericStream

REQUIREMENTS = ("hidapi",)

CONFIG_SCHEMA = {
    "vid": {"type": "integer", "required": True, "empty": False},
    "pid": {"type": "integer", "required": True, "empty": False},
    "read_size": {"type": "integer", "required": True, "empty": True},
}

# pylint: disable=c-extension-no-member


class Stream(GenericStream):
    """
    Stream module for sending to and receiving from USB HID devices.
    """

    def setup_module(self) -> None:
        # pylint: disable=import-error,import-outside-toplevel
        import hid  # type: ignore

        # Setting up the USB HID connection
        self.device = hid.device()
        vendor_id = self.config["vid"]
        product_id = self.config["pid"]
        print("Opening device:", hex(vendor_id), hex(product_id))
        self.device.open(vendor_id, product_id)
        print("Manufacturer: %s" % self.device.get_manufacturer_string())
        print("Product: %s" % self.device.get_product_string())
        print("Serial No: %s" % self.device.get_serial_number_string())
        self.device.set_nonblocking(1)

    def read(self) -> Optional[bytes]:
        data = self.device.read(self.config["read_size"])
        return bytes(data) or None

    def write(self, data: bytes) -> None:
        self.device.write(data)

    def cleanup(self) -> None:
        self.device.close()
