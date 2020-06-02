from pi_mqtt_gpio.modules import GenericSensor

#DEVICE = 0x76 # Default device I2C address
#bus = smbus.SMBus(2)

REQUIREMENTS = ("smbus2","RPi.bme280")

CONFIG_SCHEMA = {
    "i2c_bus_num": {"type": "integer", "required": True, "empty": False},
    "chip_addr": {"type": "integer", "required": True, "empty": False},
    }

SENSOR_SCHEMA = {
    "type": dict (
        type="string",
        required=False,
        empty=False,
        default="temperature",
        allowed=["temperature", "humidity", "preassure"],
    ),
}

class Sensor(GenericSensor):
    """
    Implementation of Sensor class for the LM75 temperature sensor.
    """

    def __init__(self, config):
        import smbus2
        import time
        import bme280
        self.time=time
        self.lastMeas=self.time.time()-2
        self.bme280=bme280
        self.addr=config["chip_addr"]
        self.bus=smbus2.SMBus(config["i2c_bus_num"])
        self.calibration=self.bme280.load_calibration_params(self.bus,self.addr)
        self.bmedata = self.bme280.sample(self.bus, self.addr, self.calibration)
        #print("END SETUP")

    def setup_sensor(self, config):
        return True  # nothing to do here

    def get_value(self, config):
        """get the temperature or humidity value from the sensor"""
        if (self.time.time()-self.lastMeas>2):
            print("READING BME280")
            try:
                self.bmedata = self.bme280.sample(self.bus, self.addr, self.calibration)
                self.lastMeas=self.time.time()
            except:
                print("BUS Error - data buffered")
        else:
            print("BME data buffer")

        if config["type"] == "temperature":
            return self.bmedata.temperature
        if config["type"] == "humidity":
            return self.bmedata.humidity
        if config["type"] == "preassure":
            return self.bmedata.pressure
