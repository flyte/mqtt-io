from pi_mqtt_gpio.modules import GenericSensor

#DEVICE = 0x76 # Default device I2C address
#bus = smbus.SMBus(2)

REQUIREMENTS = ("smbus",)

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
        import smbus
        import time
        from ctypes import c_short
        from ctypes import c_byte
        from ctypes import c_ubyte
        self.time=time
        self.c_short=c_short
        self.c_byte=c_byte
        self.c_ubyte=c_ubyte
        self.dig_T1 = 0
        self.dig_T2 = 0
        self.dig_T3 = 0 
        self.dig_P1 = 0 
        self.dig_P2 = 0 
        self.dig_P3 = 0
        self.dig_P4 = 0
        self.dig_P5 = 0
        self.dig_P6 = 0
        self.dig_P7 = 0
        self.dig_P8 = 0
        self.dig_P9 = 0
        self.dig_H1 = 0
        self.dig_H2 = 0
        selfdig_H3 = 0
        self.dig_H4 = 0
        self.dig_H5 = 0
        self.dig_H6 = 0
        self.bus = smbus.SMBus(config["i2c_bus_num"])
        self.address = config["chip_addr"]
        #print("SETUP BME")
        # Register Address
        REG_DATA = 0xF7
        REG_CONTROL = 0xF4
        REG_CONFIG  = 0xF5
        REG_CONTROL_HUM = 0xF2
        REG_HUM_MSB = 0xFD
        REG_HUM_LSB = 0xFE
        # Oversample setting - page 27
        OVERSAMPLE_TEMP = 2
        OVERSAMPLE_PRES = 2
        MODE = 1
        # Oversample setting for humidity register - page 26
        OVERSAMPLE_HUM = 2
        self.bus.write_byte_data(self.address, REG_CONTROL_HUM, OVERSAMPLE_HUM)
        control = OVERSAMPLE_TEMP<<5 | OVERSAMPLE_PRES<<2 | MODE
        self.bus.write_byte_data(self.address, REG_CONTROL, control)
        # Read blocks of calibration data from EEPROM
        # See Page 22 data sheet
        cal1 = self.bus.read_i2c_block_data(self.address, 0x88, 24)
        cal2 = self.bus.read_i2c_block_data(self.address, 0xA1, 1)
        cal3 = self.bus.read_i2c_block_data(self.address, 0xE1, 7)
        #print("cal data:", cal1, cal2, cal3)
        # Convert byte data to word values
        self.dig_T1 = self.getUShort(cal1, 0)
        self.dig_T2 = self.getShort(cal1, 2)
        self.dig_T3 = self.getShort(cal1, 4)
        self.dig_P1 = self.getUShort(cal1, 6)
        self.dig_P2 = self.getShort(cal1, 8)
        self.dig_P3 = self.getShort(cal1, 10)
        self.dig_P4 = self.getShort(cal1, 12)
        self.dig_P5 = self.getShort(cal1, 14)
        self.dig_P6 = self.getShort(cal1, 16)
        self.dig_P7 = self.getShort(cal1, 18)
        self.dig_P8 = self.getShort(cal1, 20)
        self.dig_P9 = self.getShort(cal1, 22)
        self.dig_H1 = self.getUChar(cal2, 0)
        self.dig_H2 = self.getShort(cal3, 0)
        self.dig_H3 = self.getUChar(cal3, 2)

        self.dig_H4 = self.getChar(cal3, 3)
        self.dig_H4 = (self.dig_H4 << 24) >> 20
        self.dig_H4 = self.dig_H4 | (self.getChar(cal3, 4) & 0x0F)

        self.dig_H5 = self.getChar(cal3, 5)
        self.dig_H5 = (self.dig_H5 << 24) >> 20
        self.dig_H5 = self.dig_H5 | (self.getUChar(cal3, 4) >> 4 & 0x0F)
 
        self.dig_H6 = self.getChar(cal3, 6)
        #print("END SETUP")

    def setup_sensor(self, config):
        return True  # nothing to do here

    def convert_to_celsius(self, value):
        return (value / 32.0) / 8.0

    def get_value(self, config):
        """get the temperature or humidity value from the sensor"""
        print("READING BME")
        temperature, preassure, humidity = self.readBME280All()
        if config["type"] == "temperature" and temperature is not None:
            return temperature
        if config["type"] == "humidity" and humidity is not None:
            return humidity
        if config["type"] == "preassure" and preassure is not None:
            return preassure
        return None

    def getShort(self, data, index):
        # return two bytes from data as a signed 16-bit value
        return self.c_short((data[index+1] << 8) + data[index]).value

    def getUShort(self, data, index):
        # return two bytes from data as an unsigned 16-bit value
        return (data[index+1] << 8) + data[index]

    def getChar(self, data, index):
        # return one byte from data as a signed char
        result = data[index]
        if result > 127:
           result -= 256
        return result

    def getUChar(self, data, index):
        # return one byte from data as an unsigned char
        result =  data[index] & 0xFF
        return result
  
    def readBME280All(self):
        # Register Address
        REG_DATA = 0xF7
        # Oversample setting - page 27
        OVERSAMPLE_TEMP = 2
        OVERSAMPLE_PRES = 2
        # Oversample setting for humidity register - page 26
        OVERSAMPLE_HUM = 2
        # Wait in ms (Datasheet Appendix B: Measurement time and current calculation)
        wait_time = 1.25 + (2.3 * OVERSAMPLE_TEMP) + ((2.3 * OVERSAMPLE_PRES) + 0.575) + ((2.3 * OVERSAMPLE_HUM)+0.575)
        self.time.sleep(wait_time/1000)  # Wait the required time  

        # Read temperature/pressure/humidity
        data = self.bus.read_i2c_block_data(self.address, REG_DATA, 8)
        pres_raw = (data[0] << 12) | (data[1] << 4) | (data[2] >> 4)
        temp_raw = (data[3] << 12) | (data[4] << 4) | (data[5] >> 4)
        hum_raw = (data[6] << 8) | data[7]

        #Refine temperature
        var1 = ((((temp_raw>>3)-(self.dig_T1<<1)))*(self.dig_T2)) >> 11
        var2 = (((((temp_raw>>4) - (self.dig_T1)) * ((temp_raw>>4) - (self.dig_T1))) >> 12) * (self.dig_T3)) >> 14
        t_fine = var1+var2
        temperature = float(((t_fine * 5) + 128) >> 8);

        # Refine pressure and adjust for temperature
        var1 = t_fine / 2.0 - 64000.0
        var2 = var1 * var1 * self.dig_P6 / 32768.0
        var2 = var2 + var1 * self.dig_P5 * 2.0
        var2 = var2 / 4.0 + self.dig_P4 * 65536.0
        var1 = (self.dig_P3 * var1 * var1 / 524288.0 + self.dig_P2 * var1) / 524288.0
        var1 = (1.0 + var1 / 32768.0) * self.dig_P1
        if var1 == 0:
         pressure=0
        else:
         pressure = 1048576.0 - pres_raw
         pressure = ((pressure - var2 / 4096.0) * 6250.0) / var1
         var1 = self.dig_P9 * pressure * pressure / 2147483648.0
         var2 = pressure * self.dig_P8 / 32768.0
         pressure = pressure + (var1 + var2 + self.dig_P7) / 16.0
       
       # Refine humidity
        humidity = t_fine - 76800.0
        humidity = (hum_raw - (self.dig_H4 * 64.0 + self.dig_H5 / 16384.0 * humidity)) * (self.dig_H2 / 65536.0 * (1.0 + self.dig_H6 / 67108864.0 * humidity * (1.0 + self.dig_H3 / 67108864.0 * humidity)))
        humidity = humidity * (1.0 - self.dig_H1 * humidity / 524288.0)
        if humidity > 100:
         humidity = 100
        elif humidity < 0:
         humidity = 0
        return temperature/100.0,pressure/100.0,humidity
