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

#### Temporary Set

You may want to set the output to a given value for a certain amount of time. This can be done using the `/set_on_ms` and `/set_off_ms` topics. If an output is already set to that value, it will stay that value for the given amount of milliseconds and then switch to the opposite.

For example, to set an output named `light` on for one second, publish `1000` as the payload to the `myprefix/output/light/set_on_ms` topic.

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

These are in fact the default values should the configuration not be provided, but they can be changed to whatever is desired. The `status_topic` will be appended to the configured `topic_prefix`, if any.
