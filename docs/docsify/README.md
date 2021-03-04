# MQTT IO

[![Discord](https://img.shields.io/discord/713749043662290974.svg?label=Chat%20on%20Discord&logo=discord&logoColor=ffffff&color=7389D8&labelColor=6A7EC2)](https://discord.gg/gWyV9W4)

Exposes general purpose inputs and outputs (GPIO), hardware sensors and serial devices to an MQTT server. Ideal for single-board computers such as the Raspberry Pi.

## Supported Hardware

Hardware support is provided by specific GPIO, Sensor and Stream modules. It's easy to add support for new hardware and the list is growing fast.

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

<!-- The following are some example configurations.

### Pins

With the following example config, switch pin 21 on by publishing to the `home/kitchen/output/lights/set` topic with a payload of `ON`, and pin 22 by publishing to `home/kitchen/output/fan/set`.

```yaml
mqtt:
  host: test.mosquitto.org
  topic_prefix: home/kitchen

gpio_modules:
  - name: pi_gpio
    module: raspberrypi

digital_outputs:
  - name: lights
    module: pi_gpio
    pin: 21 # This is specified as the GPIO.BCM standard, not GPIO.BOARD

  - name: fan
    module: pi_gpio
    pin: 22
```

Or to receive updates on the status of an input pin, subscribe to the `home/input/doorbell` topic:

```yaml
mqtt:
  host: test.mosquitto.org
  topic_prefix: home

gpio_modules:
  - name: pi_gpio
    module: raspberrypi

digital_inputs:
  - name: doorbell
    module: pi_gpio
    pin: 22
```

### Modules

The IO modules are pluggable and multiple may be used at once. For example, if you have a Raspberry PI with some GPIO pins in use and also a PCF8574 IO expander on the I2C bus, you'd list two modules in the `gpio_modules` section and set up the inputs and outputs accordingly:

```yaml
mqtt:
  host: test.mosquitto.org
  topic_prefix: home/mydevice

gpio_modules:
  - name: pi_gpio
    module: raspberrypi

  - name: pcf_expander1
    module: pcf8574
    i2c_bus_num: 1
    chip_addr: 0x20

digital_inputs:
  - name: button
    module: pi_gpio
    pin: 21  # This device is connected to pin 21 of the Raspberry PI GPIO
    pullup: yes

digital_outputs:
  - name: bell
    module: pcf_expander1
    pin: 2  # This device is connected to pin 2 of the PCF8574 IO expander
```

### Sensors

Receive updates on the value of a sensor by subscribing to the `home/sensor/<sensor input name>` topic. In the following example, this would be `home/sensor/temperature`:

```yaml
mqtt:
  host: test.mosquitto.org
  topic_prefix: home

sensor_modules:
  - name: lm75_sensor
    module: lm75
    i2c_bus_num: 1
    chip_addr: 0x48

  - name: dht22_sensor
    module: dht22
    type: AM2302
    pin: 4

  - name: bh1750_sensor
    module: bh1750
    i2c_bus_num: 1
    chip_addr: 0x23

  - name: ds18b22_sensor
    module: ds18b
    type: DS18S20
    address: 000803702e49

  - name: hcsr04_sensor
    module: hcsr04
    pin_echo: 27
    pin_trigger: 17
    burst: 10  # number of measurements for output of distance value in [cm]
    
  - name: mcp3008_sensor
    module: mcp3008

sensor_inputs:
  - name: lm75_temperature
    module: lm75_sensor
    interval: 15 # interval in seconds that a value is read from the sensor and a update is published
    digits: 4 # number of digits to round the value by

  - name: dht22_temperature 
    module: dht22_sensor
    interval: 10
    digits: 4
    type: temperature # can be temperature or humidity

  - name: dht22_humidity 
    module: dht22_sensor
    interval: 10
    digits: 4
    type: humidity

  - name: bh1750_lux
    module: bh1750_sensor
    interval: 10
    digits: 2

  - name: ds18b22_temperature
    module: ds18b22_sensor
    interval: 60
    digits: 2

  - name: hcsr04_distance
    module: hcsr04_sensor
    interval: 10  # take a measurement every 10s
    digits: 1

  - name: mcp3008_voltage
    module: mcp3008_sensor
    interval: 300
    channel: CH4 # measure on CH4 of MCP3008
```

### Streams

Transmit data by publishing to the `home/stream/<stream_name>` topic. In the following example, this would be `home/stream/serialtx`.

Receive data from a stream by subscribing to the `home/stream/<stream_name>` topic. In the following example, this would be `home/stream/serialrx`.

#### New in v2.0.0+

- The stream config has changed from requiring `stream_reads` and `stream_writes` sections to just using the `stream_modules` entry to configure both.
- Stream data is not encoded or decoded. Data read from the stream is published to MQTT in its original binary form and data received in MQTT messages is written to the stream unchanged.

```yaml
mqtt:
  host: test.mosquitto.org
  topic_prefix: home

stream_modules:
  - name: serialcomms
    module: serial
    device: /dev/ttyS0
    baud: 115200
    bytesize: 8 # Number of data bits in word. Can be: 5,6,7,8
    parity: none # Parity can be one of none,odd,even,mark,space
    stopbits: 1 # Number of stop bits. Can be: 1,1.5,2
    cleanup: no  # default: yes - Sets whether the module's `cleanup()` function will be called when the software exits
    read_interval: 1 # default: 60 - Stream read polling interval in seconds
    read: yes  # default: yes - Whether to poll the stream for incoming data and publish read data
    write: yes  # default: yes - Whether to subscribe to MQTT topic to enable writing data to the stream
```

Testing example:

```bash
# -N disables printing extra new line on each subscription
mosquitto_sub -h <broker url> -t <topic prefix>/stream/serialcomms -N

mosquitto_pub -h <broker url> -t <topic prefix>/stream/serialcomms -m "testing123\r\n"
```

### OrangePi boards

You need to specify what OrangePi board you use

```yaml
gpio_modules:
  - name: orangepi
    module: orangepi
    board: zero # Supported: ZERO, R1, ZEROPLUS, ZEROPLUS2H5, ZEROPLUS2H3, PCPCPLUS, ONE, LITE, PLUS2E, PC2, PRIME
    mode: board
```

### Home Assistant discovery

The metadata of all `sensor_inputs`, `digital_inputs` and `digital_outputs` can be published via MQTT messages to be discovered by a Home Assistant instance that is listening on the same MQTT broker:

```yaml
mqtt:
  discovery: yes
  discovery_prefix: "homeassistant" # optional
  discovery_name: "device1" # optional
```

Entries in the `ha_discovery` section of the input/output configs will be added to the discovery MQTT messages in order to improve the accuracy of the Home Assistant auto-detection e.g. `device_class` or `force_update`. See the [Home Assistant MQTT Discovery](https://www.home-assistant.io/docs/mqtt/discovery/) documentation for valid options.

```yaml
digital_inputs:
  - name: motion_sensor
    module: pi_gpio
    pin: 22
    retain: yes
    ha_discovery:
      name: PIR Garage  # optional and defaults to `name` given above
      component: binary_sensor  # optional and defaults to `binary_sensor`
      device_class: motion  # optional
      force_update: true  # or any other key / value pair home-assistant discovery
```

```yaml
digital_outputs:
  - name: lamp
    module: pi_gpio
    pin: 21
    ha_discovery:
      name: Garden light  # optional and defaults to `name` given above
      component: light  # optional and defaults to `switch`
```

```yaml
sensor_inputs:
  - name: lm75_temperature
    module: lm75_sensor
    interval: 15
    digits: 4
    ha_discovery:
      name: LM75 Temperature  # optional and defaults to `name` given above
      component: sensor  # optional and defaults to `sensor`
```

## Serving Suggestion

This project is not tied to any specific deployment method, but one recommended way is to use `virtualenv` and `supervisor`. This will launch the project at boot time and handle restarting and log file rotation. It's quite simple to set up:

If using Raspbian, install `supervisor` with `apt`.

```bash
sudo apt-get update
sudo apt-get install supervisor
```

Not strictly necessary, but it's recommended to install the project into a [virtualenv](http://docs.python-guide.org/en/latest/dev/virtualenvs/#lower-level-virtualenv). Generally, the best way to get an up-to-date version of `virtualenv` is to use `pip install --upgrade virtualenv`. If you don't already have `pip`, then [check here](https://pip.pypa.io/en/stable/installing/) for installation instructions.

```bash
cd /home/pi
virtualenv ve
. ve/bin/activate
pip install pi-mqtt-gpio
```

Create yourself a config file, following instructions and examples above, and save it somewhere, such as `/home/pi/pi-mqtt-gpio.yml`.

Create a [supervisor config file](http://supervisord.org/configuration.html#program-x-section-settings) in /etc/supervisor/conf.d/pi-mqtt-gpio.conf something along the lines of the following:

```
[program:pi_mqtt_gpio]
command = /home/pi/ve/bin/python -m pi_mqtt_gpio.server pi-mqtt-gpio.yml
directory = /home/pi
redirect_stderr = true
stdout_logfile = /var/log/pi-mqtt-gpio.log
```

Save the file and then run the following to update supervisor and start the program running.

```bash
sudo supervisorctl update
```

Check the status of your new supervisor job:

```bash
sudo supervisorctl status
```

Check the [supervisor docs](http://supervisord.org/running.html#supervisorctl-command-line-options) for more `supervisorctl` commands.

## Docker

_Current state: experimental and unmaintained_

Two images have been created for Docker. One using the x86_64 architecture (for Intel and AMD CPUs) and one for the ARM architecture (for Raspberry Pi etc.). The tags of the images are therefore `flyte/mqtt-gpio:x86_64` and `flyte/mqtt-gpio:armv7l`. These are the outputs of `uname -m` on the two platforms they've been built on. For the following examples I'll assume you're running on Raspberry Pi.

You may also run this software using Docker. You must create your config file as above, then run the docker image:

```
docker run -ti --rm -v /path/to/your/config.yml:/config.yml flyte/mqtt-gpio:armv7l
```

Or to run in the background:

```
docker run -d --name mqtt-gpio -v /path/to/your/config.yml:/config.yml flyte/mqtt-gpio:armv7l
```

You'll most likely want to use some hardware devices in your config, since that's what this project is all about. For example, if you wish to use the i2c bus, pass it through with a `--device` parameter:

```
docker run -ti --rm -v /path/to/your/config.yml:/config.yml --device /dev/i2c-0 flyte/mqtt-gpio:armv7l
```

If you aren't able to find the exact device path to use, then you can also run the docker container in `--privileged` mode which will pass all of the devices through from the host:

```
docker run -ti --rm -v /path/to/your/config.yml:/config.yml --privileged flyte/mqtt-gpio:armv7l
```

_Please raise an issue on Github if you find that any of this information is incorrect._ -->
