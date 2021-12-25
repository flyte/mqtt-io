from pi_mqtt_gpio.modules import GenericGPIO

REQUIREMENTS = ("smbus",)

CONFIG_SCHEMA = {
    "i2c_bus_num": {"type": "integer", "required": True, "empty": False}, # 1
    "dev_addr": {"type": "integer", "required": True, "empty": False}, # 0x10, 0x11, 0x12, 0x13
}

ON = 0xFF
OFF = 0x00
DIRECTIONS = None
PULLUPS = None

class GPIO(GenericGPIO):
    """
    Implementation of DockerPi 4 chanel relay.
    """
    def __init__(self, config):
        import smbus
        self.bus = smbus.SMBus(config["i2c_bus_num"])
        self.address = config["dev_addr"]

    def setup_pin(self, pin, direction, pullup, pin_config):
        pass

    def set_pin(self, pin, value):
        """ Turn on/off relay number self.relay """
        self.bus.write_byte_data(self.address, pin, value)

    def cleanup(self):
        self.bus.close()
