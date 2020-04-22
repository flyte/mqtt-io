from __future__ import print_function

from pi_mqtt_gpio.modules import GenericStream
import serial
from serial import Serial

REQUIREMENTS = ("serial",)
CONFIG_SCHEMA = {
    "device": {"type": "string", "required": True, "empty": False},
    "baud": {"type": "integer", "required": True, "empty": False},
    "bytesize": {"type": "integer", "required": True, "empty": False},
    "parity": {"type": "string", "required": True, "empty": False},
    "stopbits": {"type": "float", "required": True, "empty": False},
}

PORTS_USED = {}

BYTESIZE = {
    5: serial.FIVEBITS,
    6: serial.SIXBITS,
    7: serial.SEVENBITS,
    8: serial.EIGHTBITS
}

PARITY = {
    "none": serial.PARITY_NONE,
    "odd": serial.PARITY_ODD,
    "even": serial.PARITY_EVEN,
    "mark": serial.PARITY_MARK,
    "space": serial.PARITY_SPACE
}

STOPBITS = {
    1: serial.STOPBITS_ONE,
    1.5: serial.STOPBITS_ONE_POINT_FIVE,
    2: serial.STOPBITS_TWO
}

class Stream(GenericStream):
    """
    Implementation of stream class for outputting to STDIO.
    """

    def __init__(self, config):
        global PORTS_USED
        #print("__init__(config=%r)" % config)
        if not config['device'] in PORTS_USED:

            if not config['bytesize'] in BYTESIZE.keys():
                raise Exception("bytesize not one of: " + str(BYTESIZE.keys()))
            if not config['parity'] in PARITY.keys():
                raise Exception("parity not one of:" + str(PARITY.keys()))
            if not config['stopbits'] in STOPBITS.keys():
                raise Exception("stopbits not one of: " + str(STOPBITS.keys()))

            bytesize = BYTESIZE[config['bytesize']]
            parity = PARITY[config['parity']]
            stopbits = STOPBITS[config['stopbits']]

            self.ser = Serial(port=config['device'], baudrate=config['baud'], bytesize=bytesize, parity=parity, stopbits=stopbits, timeout=20)
            self.ser.flushInput()
            PORTS_USED[config['device']] = self.ser
        else:
            self.ser = PORTS_USED[config['device']]

    def setup_stream(self, config):
        #print("setup_stream(config=%r)" % config)
        pass

    def read(self, config):
        if (self.ser.inWaiting() <= 0):
            return None
        data = self.ser.read(self.ser.inWaiting()).decode('string_escape')
        #print("read(config=%r) = %s" % (config, data))
        return data

    def write(self, config, data):
        #print("write(config=%r, data=%s)" % (config,data))
        self.ser.write(data)
        pass

    def cleanup(self):
        for device, s in PORTS_USED:
            s.close()
            PORTS_USED.pop(device)
        pass
