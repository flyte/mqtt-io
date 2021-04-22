# Usage Scenarios

Since MQTT IO is a piece of software that ties one thing (MQTT) to another (GPIO, sensors, streams), there are endless scenarios in which it can be used. Home Automation is where the software was born, but anywhere you require programmatic control of hardware devices, MQTT IO may be of use.

The following are a few simple examples which attempt to show most of the basic configuration options in place, and how they might be used.

## Remote controlled mains sockets

A Raspberry Pi with an 8 channel PCF8574 IO chip, connected to relays which connect and disconnect the live wire to 4 mains sockets.

<!-- TODO: Tasks pending completion -@flyte at 04/03/2021, 22:31:45 -->
<!-- Add automated validation of these configs to ensure they're kept up to date -->

**Example configuration**

```yaml
mqtt:
  host: test.mosquitto.org
  port: 1883
  user: ""
  password: ""
  topic_prefix: home/livingroom/sockets

gpio_modules:
  - name: sockets_gpio
    module: pcf8574
    i2c_bus_num: 1
    chip_addr: 0x20

digital_outputs:
  - name: socket1
    module: sockets_gpio
    pin: 1
    on_payload: "ON"
    off_payload: "OFF"
    pullup: yes

  - name: socket2
    module: sockets_gpio
    pin: 2
    on_payload: "ON"
    off_payload: "OFF"
    pullup: yes

  - name: socket3
    module: sockets_gpio
    pin: 3
    on_payload: "ON"
    off_payload: "OFF"
    pullup: yes

  - name: socket4
    module: sockets_gpio
    pin: 4
    on_payload: "ON"
    off_payload: "OFF"
    pullup: yes
```

This configuration uses the PCF8574 GPIO module to set 4 GPIO pins of the PCF8574 as outputs, then subscribes to messages on an MQTT topic for each output. Sending the configured on/off payload to these topics will cause the software to turn the outputs on and off, therefore supplying power to, or removing power from the individual sockets. These sockets may then be used for any general purpose, such as powering lights, heaters or fans.

In order to turn each individual socket on and off, you'd send the following MQTT messages:

```yaml
home/livingroom/sockets/output/socket1/set: ON
```

```yaml
home/livingroom/sockets/output/socket1/set: OFF
```

By varying the `socket1` part of the topic, you're able to choose which socket you'd like to control.

## Temperature and humidity sensor

A Raspberry Pi with a DHT22 temperature and humidity sensor connected to pin 4 of its built in GPIO pins.

**Example configuration**

```yaml
mqtt:
  host: test.mosquitto.org
  port: 1883
  user: ""
  password: ""
  topic_prefix: home/livingroom/climate

sensor_modules:
  - name: dht22_sensor
    module: dht22
    type: AM2302
    pin: 4

sensor_inputs:
  - name: temperature
    module: dht22_sensor
    interval: 10
    digits: 4
    type: temperature

  - name: humidity
    module: dht22_sensor
    interval: 10
    digits: 4
    type: humidity
```

This configuration will poll the DHT22 sensor every 10 seconds and publish MQTT messages such as the following:

```yaml
home/livingroom/climate/sensor/temperature: 23
home/livingroom/climate/sensor/humidity: 45
```

## Float switch for water tank

A Beaglebone Black with a float switch connected to one of its built in GPIO pins which is pulled to ground when the water tank is full and the float switch engages.

**Example configuration**

```yaml
mqtt:
  host: test.mosquitto.org
  port: 1883
  user: ""
  password: ""
  topic_prefix: home/rainwater

gpio_modules:
  - name: beaglebone_gpio
    module: beaglebone

digital_inputs:
  - name: tank
    module: beaglebone_gpio
    pin: GPIO0_26
    on_payload: full
    off_payload: ok
    inverted: yes
    pullup: yes
```

This configuration will poll the `GPIO0_26` pin of the Beaglebone's built in GPIO and publish an MQTT message when it changes from low to high and vice versa:

```yaml
home/rainwater/input/tank: ok
home/rainwater/input/tank: full
```

<!-- TODO: Tasks pending completion -@flyte at 04/03/2021, 22:30:33 -->
<!-- Add example for serial stream -->

<!-- TODO: Tasks pending completion -@flyte at 04/03/2021, 22:32:37 -->
<!-- Add example using interrupts -->
