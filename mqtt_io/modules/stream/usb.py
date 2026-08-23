"""
USB
"""

from typing import Optional

from . import GenericStream

REQUIREMENTS = ("pyusb",)

CONFIG_SCHEMA = {
    "vid": {"type": "integer", "required": True, "empty": False},
    "pid": {"type": "integer", "required": True, "empty": False},
    "read_size": {"type": "integer", "required": True, "empty": True},
    "read_timeout": {"type": "integer", "default": 1, "required": False, "empty": True},
    "write_size": {"type": "integer", "required": True, "empty": True},
    "interface": {"type": "integer", "required": True, "empty": True},
}

# pylint: disable=c-extension-no-member


class Stream(GenericStream):
    """
    Stream module for sending to and receiving from USB devices.
    """

    def setup_module(self) -> None:
        # pylint: disable=import-error,import-outside-toplevel
        import usb.core  # type: ignore
        import usb.util  # type: ignore

        # Setting up the USB connection
        vendor_id = self.config["vid"]
        product_id = self.config["pid"]
        print("Finding device:", hex(vendor_id), hex(product_id))
        self.dev = usb.core.find(idVendor=vendor_id, idProduct=product_id)
        # was it found?
        if self.dev is None:
            raise ValueError("Device not found")
        cfg = self.dev.get_active_configuration()
        intf = cfg[(self.config["interface"], 0)]

        self.ep_in = usb.util.find_descriptor(
            intf,
            # match the first OUT endpoint
            custom_match=lambda e: usb.util.endpoint_direction(e.bEndpointAddress)
            == usb.util.ENDPOINT_IN,
        )
        assert self.ep_in is not None

        self.ep_out = usb.util.find_descriptor(
            intf,
            custom_match=lambda e: usb.util.endpoint_direction(e.bEndpointAddress)
            == usb.util.ENDPOINT_OUT,
        )
        assert self.ep_out is not None

        try:
            self.dev.detach_kernel_driver(self.config["interface"])
        except usb.core.USBError:
            pass

        try:
            self.dev.set_configuration()
        except usb.core.USBError as e:
            print("Error setting configuration:", e)

        print("Endpoint In:\n", self.ep_in)
        print("Endpoint Out:\n", self.ep_out)

    def read(self) -> Optional[bytes]:
        # pylint: disable=import-error,import-outside-toplevel
        import usb.core  # type: ignore

        try:
            result = bytes(
                self.ep_in.read(self.config["read_size"], self.config["read_timeout"])
            )
        except usb.core.USBError:
            result = None
        return result

    def write(self, data: bytes) -> None:
        byte_list = list(data)
        total_length = len(byte_list)
        chunk_size = self.config["write_size"]
        for i in range(0, total_length, chunk_size):
            chunk = byte_list[i : i + chunk_size]
            if len(chunk) < chunk_size:
                chunk.extend([0] * (chunk_size - len(chunk)))
            self.ep_out.write(chunk)

    def cleanup(self) -> None:
        # pylint: disable=import-error,import-outside-toplevel
        import usb.util  # type: ignore

        usb.util.release_interface(self.dev, self.config["interface"])
        usb.util.dispose_resources(self.dev)
