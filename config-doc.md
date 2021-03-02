# MQTT IO Configuration

The software is configured using a single YAML config file. This document details
the config options for each section and provides examples.

<!-- TOC -->

- [`mqtt`](#mqtt)
  - [mqtt.`tls`](#mqtttls)
- [`gpio_modules`](#gpio_modules)
- [`sensor_modules`](#sensor_modules)
- [`stream_modules`](#stream_modules)
- [`digital_inputs`](#digital_inputs)
  - [digital_inputs.*.`interrupt_for`](#digital_inputsinterrupt_for)
  - [digital_inputs.*.`ha_discovery`](#digital_inputsha_discovery)
- [`digital_outputs`](#digital_outputs)
  - [digital_outputs.*.`ha_discovery`](#digital_outputsha_discovery)
- [`sensor_inputs`](#sensor_inputs)
  - [sensor_inputs.*.`ha_discovery`](#sensor_inputsha_discovery)
- [`logging`](#logging)

<!-- TOC -->

# `mqtt`

```yaml
Type: dict
Required: yes
```

Contains the configuration data used for connecting to an MQTT server.

**Example:**

```yaml
mqtt:
  host: test.mosquitto.org
  port: 8883
  topic_prefix: mqtt_io
  discovery: yes
  tls:
    enabled: yes
    ca_certs: mosquitto.org.crt
    certfile: client.crt
    keyfile: client.key
```

- ## mqtt.`host`

```yaml
Type: string
Required: yes
```

Host name or IP address of the MQTT server.

- ## mqtt.`port`

```yaml
Type: integer
Required: no
Minimum value: 1
Minimum value: 65535
Default: 1883
```

Port number to connect to on the MQTT server.

- ## mqtt.`user`

```yaml
Type: string
Required: no
Default: ''
```

Username to authenticate with on the MQTT server.

- ## mqtt.`password`

```yaml
Type: string
Required: no
Default: ''
```

Password to authenticate with on the MQTT server.

- ## mqtt.`client_id`

```yaml
Type: string
Required: no
Default: ''
```

[MQTT client ID](https://www.cloudmqtt.com/blog/2018-11-21-mqtt-what-is-client-id.html) to use on the MQTT server.

- ## mqtt.`topic_prefix`

```yaml
Type: string
Required: no
Default: ''
```

Prefix to use for all topics.

> For example, a `topic_prefix` of `home/livingroom` would make a digital input
called "doorbell" publish its changes to the `home/livingroom/input/doorbell`
topic.

- ## mqtt.`clean_session`

```yaml
Type: boolean
Required: no
Default: false
```

Whether or not to start a
[clean MQTT session](https://www.hivemq.com/blog/mqtt-essentials-part-7-persistent-session-queuing-messages/)
on every MQTT connection.

- ## mqtt.`protocol`

```yaml
Type: string
Required: no
Allowed:
- '3.1'
- 3.1.1
Default: 3.1.1
```

Version of the MQTT protocol to use.

> This renders in the documentation as a float, but should always be set within quotes.

- ## mqtt.`keepalive`

```yaml
Type: integer
Required: no
Unit: seconds
Minimum value: 1
Default: 10
```

How frequently in seconds to send
[ping packets](https://www.hivemq.com/blog/mqtt-essentials-part-10-alive-client-take-over/)
to the MQTT server.

- ## mqtt.`status_topic`

```yaml
Type: string
Required: no
Default: status
```

Topic on which to send messages about the running status of this software.

> Sends the payloads configured in `status_payload_running`,
`status_payload_stopped` and `status_payload_dead`.

- ## mqtt.`status_payload_running`

```yaml
Type: string
Required: no
Default: running
```

Payload to send on the status topic when the software is running.

- ## mqtt.`status_payload_stopped`

```yaml
Type: string
Required: no
Default: stopped
```

Payload to send on the status topic when the software has exited cleanly.

- ## mqtt.`status_payload_dead`

```yaml
Type: string
Required: no
Default: dead
```

Payload to send on the status topic when the software has exited unexpectedly.

> Uses [MQTT Last Will and Testament](https://www.hivemq.com/blog/mqtt-essentials-part-9-last-will-and-testament/)
to make the server automatically send this payload if our connection fails.

- ## mqtt.`discovery`

```yaml
Type: boolean
Required: no
Default: false
```

Enable [Home Assistant MQTT discovery](https://www.home-assistant.io/docs/mqtt/discovery/)
of our configured devices.

- ## mqtt.`discovery_prefix`

```yaml
Type: string
Required: no
Default: homeassistant
```

Prefix for the Home Assistant MQTT discovery topic.

- ## mqtt.`discovery_name`

```yaml
Type: string
Required: no
Default: MQTT IO
```

Name to identify this "device" in Home Assistant.

- ## mqtt.`client_module`

```yaml
Type: string
Required: no
Default: mqtt_io.mqtt.asyncio_mqtt
```

MQTT Client implementation module path.

> There's currently only one implementation, which uses the
[asyncio-mqtt](https://github.com/sbtinstruments/asyncio-mqtt/) client.

## mqtt.`tls`

```yaml
Type: dict
Required: no
```

TLS/SSL settings for connecting to the MQTT server over an encrypted connection.

**Example:**

```yaml
mqtt:
  host: localhost
  tls:
    enabled: yes
    ca_certs: mosquitto.org.crt
    certfile: client.crt
    keyfile: client.key
```

- - ### mqtt.tls.`enabled`

```yaml
Type: boolean
Required: yes
```

Enable a secure connection to the MQTT server.

> Most of these options map directly to the
[`tls_set()` arguments](https://www.eclipse.org/paho/index.php?page=clients/python/docs/index.php#tls-set)
on the Paho MQTT client.

- - ### mqtt.tls.`ca_certs`

```yaml
Type: string
Required: no
```

Path to the Certificate Authority certificate files that are to be treated
as trusted by this client.
[More info](https://www.eclipse.org/paho/index.php?page=clients/python/docs/index.php#tls-set)

- - ### mqtt.tls.`certfile`

```yaml
Type: string
Required: no
```

Path to the PEM encoded client certificate.
[More info](https://www.eclipse.org/paho/index.php?page=clients/python/docs/index.php#tls-set)

- - ### mqtt.tls.`keyfile`

```yaml
Type: string
Required: no
```

Path to the PEM encoded client private key.
[More info](https://www.eclipse.org/paho/index.php?page=clients/python/docs/index.php#tls-set)

- - ### mqtt.tls.`cert_reqs`

```yaml
Type: string
Required: no
Allowed:
- CERT_NONE
- CERT_OPTIONAL
- CERT_REQUIRED
Default: CERT_REQUIRED
```

Defines the certificate requirements that the client imposes on the MQTT server.
[More info](https://www.eclipse.org/paho/index.php?page=clients/python/docs/index.php#tls-set)

> By default this is `CERT_REQUIRED`, which means that the broker must provide a certificate.

- - ### mqtt.tls.`tls_version`

```yaml
Type: string
Required: no
```

Specifies the version of the SSL/TLS protocol to be used.
[More info](https://www.eclipse.org/paho/index.php?page=clients/python/docs/index.php#tls-set)

> By default the highest TLS version is detected.

- - ### mqtt.tls.`ciphers`

```yaml
Type: string
Required: no
```

Which encryption ciphers are allowable for this connection.
[More info](https://www.eclipse.org/paho/index.php?page=clients/python/docs/index.php#tls-set)

- - ### mqtt.tls.`insecure`

```yaml
Type: boolean
Required: no
Default: false
```

Configure verification of the server hostname in the server certificate.
[More info](https://www.eclipse.org/paho/index.php?page=clients/python/docs/index.php#tls-insecure-set)

> If set to true, it is impossible to guarantee that the host you are
connecting to is not impersonating your server. This can be useful in
initial server testing, but makes it possible for a malicious third party
to impersonate your server through DNS spoofing, for example.
Do not use this function in a real system. Setting value to true means there
is no point using encryption.

# `gpio_modules`

```yaml
Type: list
Required: no
Default: []
```

List of GPIO modules to configure for use with inputs and/or outputs.

> Some modules require extra config entries, specified by the modules themselves.
Until the documentation is written for the individual modules, please refer to the
`CONFIG_SCHEMA` value of the module's code in
[the repository](https://github.com/flyte/pi-mqtt-gpio/tree/feature/asyncio/mqtt_io/modules).
TODO: Link this to the pending wiki pages on each module's requirements.

**Example:**

```yaml
gpio_modules:
  - name: rpi_gpio
    module: raspberrypi
  
  - name: pcf
    module: pcf8574
    i2c_bus_num: 1
    chip_addr: 0x20
```

- ## gpio_modules.`*`

```yaml
Type: dict
Required: no
Unlisted entries accepted: yes
```

- ## gpio_modules.*.`name`

```yaml
Type: string
Required: yes
```

Your name for this configuration of the module. Will be referred to by entries
in the `digital_inputs` and/or `digital_outputs` sections.

- ## gpio_modules.*.`module`

```yaml
Type: string
Required: yes
```

Name of the module in the code. This is listed in the README's
"Supported Hardware" section in brackets.

- ## gpio_modules.*.`cleanup`

```yaml
Type: boolean
Required: no
Default: true
```

Whether to run the module's `cleanup()` method on exit.

# `sensor_modules`

```yaml
Type: list
Required: no
Default: []
```

List of sensor modules to configure for use with sensor inputs.

> Some modules require extra config entries, specified by the modules themselves.
Until the documentation is written for the individual modules, please refer to the
`CONFIG_SCHEMA` value of the module's code in
[the repository](https://github.com/flyte/pi-mqtt-gpio/tree/feature/asyncio/mqtt_io/modules).
TODO: Link this to the pending wiki pages on each module's requirements.

**Example:**

```yaml
sensor_modules:
  - name: dht
    module: dht22
    type: AM2302
    pin: 4
  
  - name: ds
    module: ds18b
    type: DS18S20
    address: 000803702e49
```

- ## sensor_modules.`*`

```yaml
Type: dict
Required: no
Unlisted entries accepted: yes
```

- ## sensor_modules.*.`name`

```yaml
Type: string
Required: yes
```

Your name for this configuration of the module. Will be referred to by entries
in the `sensor_inputs` section.

- ## sensor_modules.*.`module`

```yaml
Type: string
Required: yes
```

Name of the module in the code. This is listed in the README's
"Supported Hardware" section in brackets.

- ## sensor_modules.*.`cleanup`

```yaml
Type: boolean
Required: no
Default: true
```

Whether to run the module's `cleanup()` method on exit.

# `stream_modules`

```yaml
Type: list
Required: no
Default: []
```

List of stream modules to configure.

> Some modules require extra config entries, specified by the modules themselves.
Until the documentation is written for the individual modules, please refer to the
`CONFIG_SCHEMA` value of the module's code in
[the repository](https://github.com/flyte/pi-mqtt-gpio/tree/feature/asyncio/mqtt_io/modules).
TODO: Link this to the pending wiki pages on each module's requirements.

**Example:**

```yaml
stream_modules:
  - name: network_switch
    module: serial
    device: /dev/ttyUSB1
    baud: 115200
    interval: 10

  - name: ups
    module: serial
    type: /dev/ttyUSB0
    baud: 9600
    interval: 1
```

- ## stream_modules.`*`

```yaml
Type: dict
Required: no
Unlisted entries accepted: yes
```

- ## stream_modules.*.`name`

```yaml
Type: string
Required: yes
```

Your name for this configuration of the module. Will be used in the topic on
which the stream's data is published and the topic on which messages can be
sent for writing to the stream.

- ## stream_modules.*.`module`

```yaml
Type: string
Required: yes
```

Name of the module in the code. This is listed in the README's
"Supported Hardware" section in brackets.

- ## stream_modules.*.`cleanup`

```yaml
Type: boolean
Required: no
Default: true
```

Whether to run the module's `cleanup()` method on exit.

- ## stream_modules.*.`retain`

```yaml
Type: boolean
Required: no
Default: false
```

Whether to set the `retain` flag on MQTT messages publishing data received
from the stream.

- ## stream_modules.*.`read_interval`

```yaml
Type: float
Required: no
Unit: seconds
Minimum value: 0.01
Default: 60
```

How long to wait between polling the stream for new data.

- ## stream_modules.*.`read`

```yaml
Type: boolean
Required: no
Default: true
```

Whether to poll this stream for incoming data and publish it on an MQTT topic.

- ## stream_modules.*.`write`

```yaml
Type: boolean
Required: no
Default: true
```

Whether to subscribe to MQTT messages on a topic and write messages received on it to the stream.

# `digital_inputs`

```yaml
Type: list
Required: no
Default: []
```

List of digital inputs to configure.

> Some modules require extra config entries, specified by the modules themselves.
Until the documentation is written for the individual modules, please refer to the
`PIN_SCHEMA` and `INPUT_SCHEMA` values of the module's code in
[the repository](https://github.com/flyte/pi-mqtt-gpio/tree/feature/asyncio/mqtt_io/modules).
TODO: Link this to the pending wiki pages on each module's requirements.

**Example:**

```yaml
gpio_modules:
  - name: rpi
    module: raspberrypi

digital_inputs:
  - name: gpio0
    module: rpi
    pin: 0

  - name: gpio1
    module: rpi
    pin: 1
```

- ## digital_inputs.`*`

```yaml
Type: dict
Required: no
Unlisted entries accepted: yes
```

- ## digital_inputs.*.`name`

```yaml
Type: string
Required: yes
```

Name of the input. Used in the MQTT topic when publishing input changes.

The topic that input changes will be published to is:
`<mqtt.topic_prefix>/input/<this name>`

- ## digital_inputs.*.`module`

```yaml
Type: string
Required: yes
```

Name of the module configured in `gpio_modules` that this input is attached to.

- ## digital_inputs.*.`pin`

```yaml
Type:
  - string
  - integer
Required: yes
```

Which of the GPIO module's pins this input refers to.

> Depending on the GPIO module's implementation, this can be either a string
or an integer.

- ## digital_inputs.*.`on_payload`

```yaml
Type: string
Required: no
Default: 'ON'
```

Payload to be sent when the input changes to what is considered to be "on".
See `inverted` below for the definition of "on" and "off".

> Make sure to avoid YAML's automatic boolean type conversion when setting this
option by surrounding potential booleans with quotes.
See the "Regexp" section of the
[YAML bool docs](https://yaml.org/type/bool.html) for all of the values that
will be parsed as boolean.

- ## digital_inputs.*.`off_payload`

```yaml
Type: string
Required: no
Default: 'OFF'
```

Payload to be sent when the input changes to what is considered to be "off".
See `inverted` below for the definition of "on" and "off".

> Make sure to avoid YAML's automatic boolean type conversion when setting this
option by surrounding potential booleans with quotes.
See the "Regexp" section of the
[YAML bool docs](https://yaml.org/type/bool.html) for all of the values that
will be parsed as boolean.

- ## digital_inputs.*.`inverted`

```yaml
Type: boolean
Required: no
Default: false
```

Invert the logic level so that "low" levels are considered to be "on" and
"high" levels are considered "off".

> This can be useful for when an input is pulled "high" with a resistor and a
device (like a button or another IC) connects it to ground when it's "active".

- ## digital_inputs.*.`pullup`

```yaml
Type: boolean
Required: no
Default: false
```

Enable the pull-up resistor for this input so that the logic level is pulled
"high" by default.

> Not all GPIO modules support pull-up resistors.

- ## digital_inputs.*.`pulldown`

```yaml
Type: boolean
Required: no
Default: false
```

Enable the pull-down resistor for this input so that the logic level is pulled
"low" by default.

> Not all GPIO modules support pull-down resistors.

- ## digital_inputs.*.`interrupt`

```yaml
Type: string
Required: no
Allowed:
- rising
- falling
- both
```

Configure this pin to trigger an interrupt when the logic level is "rising",
"falling" or "both".

> Not all GPIO modules support interrupts, and those that do may do so in
various ways.
TODO: Add link to interrupt documentation.

## digital_inputs.*.`interrupt_for`

```yaml
Type: list
Required: no
```

List of other pin names that this pin is an interrupt for.

This is generally used on GPIO modules that provide software callbacks on
interrupts, so that we can attach another "remote" module's interrupt output
pin (one that changes logic level when one of its pins triggers an interrupt)
to this input and use the callback to get the value of the "remote" pin and
publish it on MQTT.

TODO: Add link to interrupt documentation.

- - ### digital_inputs.*.interrupt_for.`*`

```yaml
Type: string
Required: yes
```

- ## digital_inputs.*.`bouncetime`

```yaml
Type: integer
Required: no
Unit: milliseconds
Minimum value: 1
Default: 100
```

Don't trigger interrupts more frequently than once per `bouncetime`.

- ## digital_inputs.*.`retain`

```yaml
Type: boolean
Required: no
Default: false
```

Set the retain flag on MQTT messages published on input change.

- ## digital_inputs.*.`poll_interval`

```yaml
Type: float
Required: no
Unit: seconds
Default: 0.1
```

How long to wait between checking the value of this input.

> When the pin is configured as an interrupt, the pin is no longer polled.
The only exception to this is if the pin is configured as an interrupt for
another pin. In this case, whether or not we poll is decided by the
`poll_when_interrupt_for` setting below.

- ## digital_inputs.*.`poll_when_interrupt_for`

```yaml
Type: boolean
Required: no
Default: true
```

Poll this pin when it's configured as an interrupt for another pin.

> Polling the pin when it's configured as an interrupt for another pin is useful
in order to make sure that if we somehow miss an interrupt on this pin (the
remote module's interrupt output pin goes low ("triggered")), we
don't end up stuck in that state where we don't handle the remote module's
interrupt at all. If we poll the "triggered" value on this pin and our
interrupt handling hasn't dealt with it, then we'll handle it here.

## digital_inputs.*.`ha_discovery`

```yaml
Type: dict
Required: no
Unlisted entries accepted: yes
```

Configures the
[Home Assistant MQTT discovery](https://www.home-assistant.io/docs/mqtt/discovery/)
for this pin.

Any values entered into this section will be sent as part of the discovery
config payload. See the above link for documentation.

**Example:**

```yaml
digital_inputs:
  - name: livingroom_motion
    module: rpi
    ha_discovery:
      component: binary_sensor
      name: Living Room Motion
      device_class: motion
```

- - ### digital_inputs.*.ha_discovery.`component`

```yaml
Type: string
Required: no
Default: binary_sensor
```

Type of component to report this input as to Home Assistant.

# `digital_outputs`

```yaml
Type: list
Required: no
Default: []
```

List of digital outputs to configure.

> Some modules require extra config entries, specified by the modules themselves.
Until the documentation is written for the individual modules, please refer to the
`PIN_SCHEMA` and `OUTPUT_SCHEMA` values of the module's code in
[the repository](https://github.com/flyte/pi-mqtt-gpio/tree/feature/asyncio/mqtt_io/modules).
TODO: Link this to the pending wiki pages on each module's requirements.

**Example:**

```yaml
gpio_modules:
  - name: rpi
    module: raspberrypi

digital_outputs:
  - name: gpio0
    module: rpi
    pin: 0

  - name: gpio1
    module: rpi
    pin: 1
```

- ## digital_outputs.`*`

```yaml
Type: dict
Required: no
Unlisted entries accepted: yes
```

- ## digital_outputs.*.`name`

```yaml
Type: string
Required: yes
```

Name of the output. Used in the MQTT topics that are subscribed to in order to
change the output value according to received MQTT messages, as well as in the
MQTT topic for publishing output changes.

The topics subscribed to for each output are:
- `<mqtt.topic_prefix>/output/<this name>/set`
- `<mqtt.topic_prefix>/output/<this name>/set_on_ms`
- `<mqtt.topic_prefix>/output/<this name>/set_off_ms`

The topic that output changes will be published to is:
`<mqtt.topic_prefix>/output/<this name>`

- ## digital_outputs.*.`module`

```yaml
Type: string
Required: yes
```

Name of the module configured in `gpio_modules` that this output is attached to.

- ## digital_outputs.*.`pin`

```yaml
Type:
  - string
  - integer
Required: yes
```

Which of the GPIO module's pins this output refers to.

> Depending on the GPIO module's implementation, this can be either a string
or an integer.

- ## digital_outputs.*.`on_payload`

```yaml
Type: string
Required: no
Default: 'ON'
```

Payload to consider as "on" when received to the `/set` topic for this output.
See `inverted` below for the definition of "on" and "off".

> Make sure to avoid YAML's automatic boolean type conversion when setting this
option by surrounding potential booleans with quotes.
See the "Regexp" section of the
[YAML bool docs](https://yaml.org/type/bool.html) for all of the values that
will be parsed as boolean.

- ## digital_outputs.*.`off_payload`

```yaml
Type: string
Required: no
Default: 'OFF'
```

Payload to consider as "off" when received to the `/set` topic for this output.
See `inverted` below for the definition of "on" and "off".

> Make sure to avoid YAML's automatic boolean type conversion when setting this
option by surrounding potential booleans with quotes.
See the "Regexp" section of the
[YAML bool docs](https://yaml.org/type/bool.html) for all of the values that
will be parsed as boolean.

- ## digital_outputs.*.`inverted`

```yaml
Type: boolean
Required: no
Default: false
```

Invert the logic level so that "low" levels are considered to be "on" and
"high" levels are considered "off".

> This can be useful for when an output turns something on when its output is
"low".

- ## digital_outputs.*.`timed_set_ms`

```yaml
Type: integer
Required: no
Unit: milliseconds
```

How long to set an output to the desired value on receipt of an MQTT message
to the `/set` topic before then setting it back to the opposite value.

> This may be useful if the output controls a device where leaving the ouput
"on" for too long would be detrimental. Using this option means that you don't
have to rely on a second "off" message getting through MQTT for the output to
return to a safe state.

- ## digital_outputs.*.`initial`

```yaml
Type: string
Required: no
Allowed:
- high
- low
```

Set the output to an initial "high" or "low" state when the software starts.

- ## digital_outputs.*.`publish_initial`

```yaml
Type: boolean
Required: no
Default: false
```

Whether to publish an MQTT message for the initial "high" or "low" state set
above.

- ## digital_outputs.*.`retain`

```yaml
Type: boolean
Required: no
Default: false
```

Set the retain flag on MQTT messages published on output change.

## digital_outputs.*.`ha_discovery`

```yaml
Type: dict
Required: no
Unlisted entries accepted: yes
```

Configures the
[Home Assistant MQTT discovery](https://www.home-assistant.io/docs/mqtt/discovery/)
for this pin.

Any values entered into this section will be sent as part of the discovery
config payload. See the above link for documentation.

**Example:**

```yaml
digital_outputs:
  - name: garage_door1
    module: rpi
    ha_discovery:
      component: switch
      name: Ferrari Garage Door
      device_class: garage_door
```

- - ### digital_outputs.*.ha_discovery.`component`

```yaml
Type: string
Required: no
Default: switch
```

Type of component to report this output as to Home Assistant.

# `sensor_inputs`

```yaml
Type: list
Required: no
Default: []
```

List of sensor inputs to configure.

> Some modules require extra config entries, specified by the modules themselves.
Until the documentation is written for the individual modules, please refer to the
`MODULE_SCHEMA` values of the module's code in
[the repository](https://github.com/flyte/pi-mqtt-gpio/tree/feature/asyncio/mqtt_io/modules).
TODO: Link this to the pending wiki pages on each module's requirements.

**Example:**

```yaml
sensor_modules:
  - name: dht
    module: dht22
    type: AM2302
    pin: 4

sensor_inputs:
  - name: workshop_temp
    module: dht
    type: temperature
    interval: 30

  - name: workshop_humidity
    module: dht
    type: humidity
    interval: 60
```

- ## sensor_inputs.`*`

```yaml
Type: dict
Required: no
Unlisted entries accepted: yes
```

- ## sensor_inputs.*.`name`

```yaml
Type: string
Required: yes
```

Name of the sensor. Used in the MQTT topic when publishing sensor values.

The topic that sensor values will be published to is:
`<mqtt.topic_prefix>/sensor/<this name>`

- ## sensor_inputs.*.`module`

```yaml
Type: string
Required: yes
```

Name of the module configured in `sensor_modules` that this sensor reading
comes from.

- ## sensor_inputs.*.`retain`

```yaml
Type: boolean
Required: no
Default: false
```

Set the retain flag on MQTT messages published on sensor read.

- ## sensor_inputs.*.`interval`

```yaml
Type: integer
Required: no
Unit: seconds
Minimum value: 1
Default: 60
```

How long to wait between checking the value of this sensor.

- ## sensor_inputs.*.`digits`

```yaml
Type: integer
Required: no
Minimum value: 0
Default: 2
```

How many decimal places to round the sensor reading to.

## sensor_inputs.*.`ha_discovery`

```yaml
Type: dict
Required: no
Unlisted entries accepted: yes
```

Configures the
[Home Assistant MQTT discovery](https://www.home-assistant.io/docs/mqtt/discovery/)
for this sensor.

Any values entered into this section will be sent as part of the discovery
config payload. See the above link for documentation.

**Example:**

```yaml
sensor_inputs:
  - name: workshop_temp
    module: dht
    type: temperature
    ha_discovery:
      name: Workshop Temperature
      device_class: temperature

  - name: workshop_humidity
    module: dht
    type: humidity
    ha_discovery:
      name: Workshop Humidity
      device_class: humidity
```

- - ### sensor_inputs.*.ha_discovery.`component`

```yaml
Type: string
Required: no
Default: sensor
```

Type of component to report this sensor as to Home Assistant.

- - ### sensor_inputs.*.ha_discovery.`expire_after`

```yaml
Type: integer
Required: no
Minimum value: 1
```

How long after receiving a sensor update to declare it invalid.

> Defaults to `interval` * 2 + 5

# `logging`

```yaml
Type: dict
Required: no
Unlisted entries accepted: yes
Default:
  formatters:
    default:
      datefmt: '%Y-%m-%d %H:%M:%S'
      format: '%(asctime)s %(name)s [%(levelname)s] %(message)s'
  handlers:
    console:
      class: logging.StreamHandler
      formatter: default
      level: INFO
  loggers:
    mqtt_io:
      handlers:
      - console
      level: INFO
      propagate: true
  version: 1
```

Config to pass directly to
[Python's logging module](https://docs.python.org/3/library/logging.config.html#logging-config-dictschema)
to influence the logging output of the software.