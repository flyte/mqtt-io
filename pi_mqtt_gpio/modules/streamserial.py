from __future__ import print_function

from pi_mqtt_gpio.modules import GenericStream
from serial import Serial

REQUIREMENTS = ("serial",)
CONFIG_SCHEMA = {
    "device": {"type": "string", "required": True, "empty": False},
    "baud": {"type": "integer", "required": True, "empty": False},
}

PORTS_USED = {}

class Stream(GenericStream):
    """
    Implementation of stream class for outputting to STDIO.
    """

    def __init__(self, config):
        global PORTS_USED
        #print("__init__(config=%r)" % config)
        if not config['device'] in PORTS_USED:
            self.ser = Serial(config['device'], config['baud'], timeout=20)
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
