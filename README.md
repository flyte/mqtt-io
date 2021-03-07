# MQTT IO

[![Discord](https://img.shields.io/discord/713749043662290974.svg?label=Chat%20on%20Discord&logo=discord&logoColor=ffffff&color=7389D8&labelColor=6A7EC2)](https://discord.gg/gWyV9W4)

Exposes general purpose IO (GPIO), hardware sensors and serial devices to an MQTT server, enabling remote monitoring and control. This allows pins to be read and switched by reading or writing messages to MQTT topics. Streams and sensors will be read periodically and publish their values.

Visit the [documentation](https://flyte.github.io/mqtt-io/) for more detailed information.

## Supported Hardware

### GPIO Modules

- Raspberry Pi GPIO (`raspberrypi`)
- Orange Pi GPIO (`orangepi`)
- PCF8574 IO chip (`pcf8574`)
- PCF8575 IO chip (`pcf8575`)
- PiFaceDigital 2 IO board (`piface2`)
- Beaglebone GPIO (`beaglebone`)
- Linux Kernel 4.8+ libgpiod (`gpiod`)

### Sensors

- LM75 i2c temperature sensor (`lm75`)
- DHT11 DHT22 AM2302 temperature/humidity sensor (`dht22`)
- BH1750 light level sensor (`bh1750`)
- DS18S20, DS1822, DS18B20, DS1825, DS28EA00, MAX31850K one-wire temperature sensors: (`ds18b`)
- HC-SR04 ultrasonic distance sensor (`hcsr04`)
- MCP3008 analog digital converter (`mcp3008`)
- BME280 temperature, humidity and pressure sensor (`bme280`)
- BME680 temperature, humidity and pressure sensor (`bme680`)

### Streams

- Serial port (`serial`)

## Installation

_Requires Python 3.6+_

`pip3 install mqtt-io`

## Execution

`python3 -m mqtt-io config.yml`

## Configuration

Configuration is handled by a YAML file which is passed as an argument to the server on startup.

See the [documentation](https://flyte.github.io/mqtt-io/) for more detail.
