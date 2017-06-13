PI MQTT GPIO
============

Expose the Raspberry Pi GPIO pins (and/or external IO modules such as the PCF8574) to an MQTT server. This allows pins to be read and switched by reading or writing messages to MQTT topics.

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

With the following example config, switch pin 21 on by publishing to the `home/kitchen/output/lights/set` topic with a payload of `ON`.

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

digital_inputs:
  - name: doorbell
    module: raspberrypi
    pin: 22
    on_payload: "ON"
    off_payload: "OFF"
    pullup: yes
    pulldown: no
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
