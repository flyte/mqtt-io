<!--
***************************************************************************************
DO NOT EDIT README.md DIRECTLY, IT'S GENERATED FROM README.md.j2 USING generate_docs.py
***************************************************************************************
-->

# MQTT IO

[![Discord](https://img.shields.io/discord/713749043662290974.svg?label=Chat%20on%20Discord&logo=discord&logoColor=ffffff&color=7389D8&labelColor=6A7EC2)](https://discord.gg/gWyV9W4)

Exposes general purpose inputs and outputs (GPIO), hardware sensors and serial devices to an MQTT server. Ideal for single-board computers such as the Raspberry Pi.

Visit the [documentation](https://mqtt-io.app/) for more detailed information.

## Supported Hardware

Hardware support is provided by specific GPIO, Sensor and Stream modules. It's easy to add support for new hardware and the list is growing fast.

### GPIO Modules

  - Beaglebone GPIO (`beaglebone`)
  - DockerPi 4 Channel Relay GPIO (`dockerpi`)
  - Linux Kernel 4.8+ libgpiod (`gpiod`)
  - GPIO Zero (`gpiozero`)
  - MCP23017 IO expander (`mcp23017`)
  - Orange Pi GPIO (`orangepi`)
  - PCF8574 IO expander (`pcf8574`)
  - PCF8575 IO expander (`pcf8575`)
  - PiFace Digital IO 2 (`piface2`)
  - Raspberry Pi GPIO (`raspberrypi`)
<<<<<<< HEAD
  - Sunxi Board (`sunxi`)
=======
  - XL9535/PCA9535/TCA9535 IO expander (`xl9535`)
>>>>>>> upstream/develop

### Sensors

  - ADS1x15 analog to digital converters (`ads1x15`)
<<<<<<< HEAD
  - ADXL345 Digital Accelerometer Sensor (`adxl345`)
=======
  - ADXl345 3-axis accelerometer up to ±16g  (`adxl345`)
>>>>>>> upstream/develop
  - AHT20 temperature and humidity sensor (`aht20`)
  - AS3935 lightning detector (`as3935`)
  - BH1750 light level sensor (`bh1750`)
  - BME280 temperature, humidity and pressure sensor (`bme280`)
  - BME680 temperature, humidity and pressure sensor (`bme680`)
  - BMP085 temperature and pressure sensor (`bmp085`)
  - DHT11/DHT22/AM2302 temperature and humidity sensors (`dht22`)
  - DS18S20/DS1822/DS18B20/DS1825/DS28EA00/MAX31850K temperature sensors (`ds18b`)
<<<<<<< HEAD
  - ENS160 Air Quality Sensor (`ens160`)
  - Flowsensor: Generic Flow Rate Sensor (`flowsensor`)
  - Frequencycounter: Generic Frequency Counter (`frequencycounter`)
=======
  - ENS160  digital multi-gas sensor with multiple IAQ data (TVOC, eCO2, AQI) (`ens160`)
  - FLOWSENSOR generic flow rate sensor like YF-S201, YF-DN50 or others (`flowsensor`)
  - FREQUENCYCOUNTER Counts pulses from GPIOs and return the frequency in Hz (`frequencycounterr`)
>>>>>>> upstream/develop
  - HCSR04 ultrasonic range sensor (connected to the Raspberry Pi on-board GPIO) (`hcsr04`)
  - INA219 DC current sensor (`ina219`)
  - LM75 temperature sensor (`lm75`)
  - MCP3008 analog to digital converter (`mcp3008`)
<<<<<<< HEAD
  - MCP3xxx analog to digital converter via GPIOZero (`mcp3xxx`)
  - MH-Z19 NDIR CO2 sensor (`mhz19`)
  - PMS5003 Particulate Matter Sensor (`pms5003`)
  - SHT4x temperature and humidity sensor (`sht4x`)
  - TSL2561 luminosity sensor (`tsl2561`)
  - VEML 6075 UV sensor (`veml6075`)
  - VEML7700 luminosity sensor (`veml7700`)
=======
  - PMS5003 particulate sensor (`pms5003`)
  - SHT40/SHT41/SHT45 temperature and humidity sensors (`sht4x`)
  - TSL2561 light level sensor (`tsl2561`)
  - VEML7700 light level sensor (`veml7700`)
  - YF-S201 flow rate sensor (`yfs201`)

>>>>>>> upstream/develop

### Streams

  - PN532 NFC/RFID reader (`pn532`)
  - Serial port (`serial`)

## Installation

_Requires Python 3.6+_

`pip3 install mqtt-io`

## Execution

`python3 -m mqtt_io config.yml`

Some configuration parameters can be passed as environment variables:

- `MQTT_IO_HOST` - Host name or IP address of the MQTT server.
- `MQTT_IO_PORT` - Port number to connect to on the MQTT server.
- `MQTT_IO_USER` - Username to authenticate with on the MQTT server.
- `MQTT_IO_PASSWORD` - Password to authenticate with on the MQTT server.
- `MQTT_IO_PROTOCOL` - Version of the MQTT protocol to use.

Environment variables take precedence over configuration files.

## Configuration Example

Configuration is written in a YAML file which is passed as an argument to the server on startup.

See the [full configuration documentation](https://github.com/flyte/pi-mqtt-gpio/wiki/Configuration) for details.

The following example will configure the software to do the following:

- Publish MQTT messages on the `home/input/doorbell` topic when the doorbell is pushed and released.
- Subscribe to the MQTT topic `home/output/port_light/set` and change the output when messages are received on it.
- Periodically read the value of the LM75 sensor and publish it on the MQTT topic `home/sensor/porch_temperature`.
- Publish any data received on the `/dev/ttyUSB0` serial port to the MQTT topic `home/serial/alarm_system`.
- Subscribe to the MQTT topic `home/serial/alarm_system/send` and send any data received on that topic to the serial port.

```yaml
mqtt:
  host: localhost
  topic_prefix: home

# GPIO
gpio_modules:
  # Use the Raspberry Pi built-in GPIO
  - name: rpi
    module: raspberrypi

digital_inputs:
  # Pin 0 is an input connected to a doorbell button
  - name: doorbell
    module: rpi
    pin: 0

digital_outputs:
  # Pin 1 is an output connected to a light
  - name: porch_light
    module: rpi
    pin: 1

# Sensors
sensor_modules:
  # An LM75 sensor attached to the I2C bus
  - name: lm75_sensor
    module: lm75
    i2c_bus_num: 1
    chip_addr: 0x48

sensor_inputs:
  # The configuration of the specific sensor value to use (LM75 only has temperature)
  - name: porch_temperature
    module: lm75_sensor

# Streams
stream_modules:
  # A serial port to communicate with the house alarm system
  - name: alarm_system
    module: serial
    device: /dev/ttyUSB0
    baud: 9600
```
