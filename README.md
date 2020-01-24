PI MQTT GPIO
============

[![Gitter](https://badges.gitter.im/mqtt-io/community.svg)](https://gitter.im/mqtt-io/community?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge)

Expose the Raspberry Pi GPIO pins, external IO modules and I2C sensors to an MQTT server. This allows pins to be read and switched by reading or writing messages to MQTT topics. The I2C sensors will be read periodically and publish their values. 

GPIO Modules
------------

- Raspberry Pi GPIO (`raspberrypi`)
- Orange Pi GPIO (`orangepi`)
- PCF8574 IO chip (`pcf8574`)
- PiFaceDigital 2 IO board (`piface2`)
- Beaglebone GPIO (`beaglebone`)

Sensors
-------

- LM75 i2c temperature sensor (`lm75`)
- DHT11 DHT22 AM2302 temperature/humidity sensor (`dht22`)
- BH1750 light level sensor (`bh1750`)
- DS18S20, DS1822, DS18B20, DS1825, DS28EA00, MAX31850K one-wire temperature sensors: (`ds18b`)

Installation
------------

`pip install pi-mqtt-gpio`

Execution
---------
`python -m pi_mqtt_gpio.server config.yml`

Configuration
-------------

Configuration is handled by a YAML file which is passed as an argument to the server on startup.

### Pins

With the following example config, switch pin 21 on by publishing to the `home/kitchen/output/lights/set` topic with a payload of `ON`, and pin 22 by publishing to `home/kitchen/output/fan/set`.

```yaml
mqtt:
  host: test.mosquitto.org
  port: 1883
  user: ""
  password: ""
  topic_prefix: home/kitchen

gpio_modules:
  - name: raspberrypi
    module: raspberrypi

digital_outputs:
  - name: lights
    module: raspberrypi
    pin: 21
    on_payload: "ON"
    off_payload: "OFF"
    initial: low  # This optional value controls the initial state of the pin before receipt of any messages from MQTT. Valid options are 'low' and 'high'.
    retain: yes # This option value controls if the message is retained. Default is no.

  - name: fan
    module: raspberrypi
    pin: 22
    inverted: yes  # This pin may control an open-collector output which is "on" when the output is "low".
    on_payload: "ON"
    off_payload: "OFF"
```

Or to receive updates on the status of an input pin, subscribe to the `home/input/doorbell` topic:

```yaml
mqtt:
  host: test.mosquitto.org
  port: 1883
  user: ""
  password: ""
  topic_prefix: home

gpio_modules:
  - name: raspberrypi
    module: raspberrypi
    cleanup: no  # This optional boolean value sets whether the module's `cleanup()` function will be called when the software exits.

digital_inputs:
  - name: doorbell
    module: raspberrypi
    pin: 22
    on_payload: "ON"
    off_payload: "OFF"
    pullup: yes
    pulldown: no
```
### Sensors

Receive updates on the value of a sensor by subscribing to the `home/sensor/<sensor input name>` topic. In the following example, this would be `home/sensor/temperature`:

```yaml
mqtt:
  host: test.mosquitto.org
  port: 1883
  user: ""
  password: ""
  topic_prefix: home

sensor_modules:
  - name: lm75
    module: lm75
    i2c_bus_num: 1
    chip_addr: 0x48
    cleanup: no  # This optional boolean value sets whether the module's `cleanup()` function will be called when the software exits.

sensor_inputs:
  - name: temperature
    module: lm75
    interval: 15 #interval in seconds, that a value is read from the sensor and a update is published
    digits: 4 # number of digits to be round
    

sensor_modules:
  - name: dht22
    module: dht22
    type: AM2302 # can be  DHT11, DHT22 or AM2302
    pin: 4

sensor_inputs:
  - name: dht22_temperature 
    module: dht22
    interval: 10 #interval in seconds, that a value is read from the sensor and a update is published
    digits: 4 # number of digits to be round
    type: temperature # Can be temperature or humidity
      
  - name: dht22_humidity 
    module: dht22
    interval: 10 #interval in seconds, that a value is read from the sensor and a update is published
    digits: 4 # number of digits to be round
    type: humidity # Can be temperature or humidity   

sensor_modules:
  - name: bh1750
    module: bh1750
    i2c_bus_num: 1
    chip_addr: 0x23

sensor_inputs:
  - name: bh1750_lux
    module: bh1750
    interval: 10
    digits: 2
    
sensor_modules:
  - name: ds18b22
    module: ds18b
    type: DS18S20
    address: 000803702e49

sensor_inputs:
  - name: ds18b22
    module: ds18b22
    interval: 60
    digits: 2
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

#### SSL/TLS

You may want to connect to a remote server, in which case it's a good idea to use an encrypted connection. If the server supports this, then you can supply the relevant config values for the [tls_set()](https://github.com/eclipse/paho.mqtt.python#tls_set) command.

```yaml
mqtt:
  host: test.mosquitto.org
  port: 8883
  tls:
    enabled: yes
```

You may need to supply a trusted CA certificate, as instructed on https://test.mosquitto.org/.

```yaml
mqtt:
  host: test.mosquitto.org
  port: 8883
  tls:
    enabled: yes
    ca_certs: mosquitto.org.crt
```

Or you might want to use SSL/TLS but not verify the server's certificate (not recommended).

```yaml
mqtt:
  host: test.mosquitto.org
  port: 8883
  tls:
    enabled: yes
    cert_reqs: CERT_NONE
    insecure: yes
```

#### Temporary Set

You may want to set the output to a given value for a certain amount of time. This can be done using the `/set_on_ms` and `/set_off_ms` topics. If an output is already set to that value, it will stay that value for the given amount of milliseconds and then switch to the opposite.

For example, to set an output named `light` on for one second, publish `1000` as the payload to the `myprefix/output/light/set_on_ms` topic.

If you want to force an output to always set to on/off for a configured amount of time, you can add `timed_set_ms` to your output config. This will mean that if you send "ON" to `myprefix/output/light/set`, then it will turn the light on for however many milliseconds are configured in `timed_set_ms` and then turn it off again. Whether the light is on already or not, sending "ON" will make the light eventually turn off after `timed_set_ms` milliseconds. This also works inversely with sending "OFF", which will turn the light off, then on after `timed_set_ms` milliseconds, so don't expect this to always keep your devices set to on/off.

#### Interrupts

Interrupts may be used for inputs instead of polling for raspberry modules. Specify `interrupt` and a strategy `rising`, `falling` or `both` to switch from polling to interrupt mode. The `bouncetime` is default `100ms` but may be changed (at least 1ms). The interrupt trigger will send a configurable `interrupt_payload` (default: `"INT"`) and not the current value of the pin: reading the current pin value in the ISR, returned 'old' values. Reading again in the ISR after 100ms gave 'changed' value, but waiting in ISR is not a good solution. So only a trigger message is transmitted on each ISR trigger.

```yaml
digital_inputs:
  - name: button_left
    module: raspberrypi
    pin: 23
    interrupt_payload: "trigger"
    pullup: no
    pulldown: yes
    interrupt: falling
    bouncetime: 200
```

### Modules

The IO modules are pluggable and multiple may be used at once. For example, if you have a Raspberry PI with some GPIO pins in use and also a PCF8574 IO expander on the I2C bus, you'd list two modules in the `gpio_modules` section and set up the inputs and outputs accordingly:

```yaml
mqtt:
  host: test.mosquitto.org
  port: 1883
  user: ""
  password: ""
  topic_prefix: pimqttgpio/mydevice

gpio_modules:
  - name: raspberrypi
    module: raspberrypi

  - name: pcf8574
    module: pcf8574
    i2c_bus_num: 1
    chip_addr: 0x20

  - name: orangepi
    module: orangepi
    board: r1
    mode: board

digital_inputs:
  - name: button
    module: raspberrypi
    pin: 21  # This device is connected to pin 21 of the Raspberry PI GPIO
    on_payload: "ON"
    off_payload: "OFF"
    pullup: no
    pulldown: yes

digital_outputs:
  - name: bell
    module: pcf8574
    pin: 2  # This device is connected to pin 2 of the PCF8574 IO expander
    on_payload: "ON"
    off_payload: "OFF"
```

### MQTT Status Topic

MQTT supports a "last will and testament" (LWT) feature which means the server will publish to a configured topic with a message of your choosing if it loses connection to the client unexpectedly. Using this feature, this project can be configured to publish to a status topic as depicted in the following example config:

```yaml
mqtt:
  ...
  status_topic: status
  status_payload_running: running
  status_payload_stopped: stopped
  status_payload_dead: dead
```

These are in fact the default values should the configuration not be provided, but they can be changed to whatever is desired. The `status_topic` will be appended to the configured `topic_prefix`, if any. For example, with the following config:

```yaml
mqtt:
  ...
  topic_prefix: home/office
  status_topic: status
```

the status messages will appear on topic `home/office/status`.

### Logging

Logging may be configured by including a `logging` section in your `config.yml`. The standard Python logging system is used, so configuration questions should be answered by looking at [the Python logging howto](https://docs.python.org/3/howto/logging.html).

The default config is set as follows. If you wish to change this, copy and paste this section into your `config.yml` and change whichever parts you'd like.

```yaml
logging:
  version: 1
  formatters:
    simple:
      format: "%(asctime)s %(name)s (%(levelname)s): %(message)s"
  handlers:
    console:
      class: logging.StreamHandler
      level: DEBUG
      formatter: simple
      stream: ext://sys.stdout
  loggers:
    mqtt_gpio:
      level: INFO
      handlers: [console]
      propagate: yes
```

Serving Suggestion
------------------

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

Docker
------

You may also run this software using Docker. You must create your config file as above, then run the docker image:

```
docker run -ti --rm -v /path/to/your/config.yml:/config.yml flyte/mqtt-gpio
```

Or to run in the background:

```
docker run -d --name mqtt-gpio -v /path/to/your/config.yml:/config.yml flyte/mqtt-gpio
```

You'll most likely want to use some hardware devices in your config, since that's what this project is all about. For example, if you wish to use the i2c bus, pass it through with a `--device` parameter:

```
docker run -ti --rm -v /path/to/your/config.yml:/config.yml --device /dev/i2c-0 flyte/mqtt-gpio
```

If you aren't able to find the exact device path to use, then you can also run the docker container in `--privileged` mode which will pass all of the devices through from the host:

```
docker run -ti --rm -v /path/to/your/config.yml:/config.yml --privileged flyte/mqtt-gpio
```

_Please raise an issue on Github if any of this information is incorrect._
