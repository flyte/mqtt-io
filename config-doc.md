# MQTT IO Configuration

Description stuff...
<!--schema_section(depth=0)-->
<!--cerberus_section(depth=0)-->

## `mqtt`

-------------------

```yaml
Type: dict
Required: yes
```

Contains the configuration data used for connecting to an MQTT server.

### Section options:
<!--schema_section(depth=1)-->
<!--cerberus_section(depth=1)-->

- ### <small>_mqtt_.</small>`host`

```yaml
Type: string
Required: yes
```

Host name or IP address of the MQTT server.
<!--cerberus_section(depth=1)-->

- ### <small>_mqtt_.</small>`port`

```yaml
Type: integer
Required: no
Default: 1883
Minimum value: 1
Minimum value: 65535
```

Port number to connect to on the MQTT server.
<!--cerberus_section(depth=1)-->

- ### <small>_mqtt_.</small>`user`

```yaml
Type: string
Required: no
```

Username to authenticate with on the MQTT server.
<!--cerberus_section(depth=1)-->

- ### <small>_mqtt_.</small>`password`

```yaml
Type: string
Required: no
```

Password to authenticate with on the MQTT server.
<!--cerberus_section(depth=1)-->

- ### <small>_mqtt_.</small>`client_id`

```yaml
Type: string
Required: no
```

[MQTT client ID](https://www.cloudmqtt.com/blog/2018-11-21-mqtt-what-is-client-id.html) to use on the MQTT server.
<!--cerberus_section(depth=1)-->

- ### <small>_mqtt_.</small>`topic_prefix`

```yaml
Type: string
Required: no
```

Prefix to use for all topics.

> For example, a `topic_prefix` of `home/livingroom` would make a digital input
called "doorbell" publish its changes to the `home/livingroom/input/doorbell`
topic.
<!--cerberus_section(depth=1)-->

- ### <small>_mqtt_.</small>`clean_session`

```yaml
Type: boolean
Required: no
```

Whether or not to start a
[clean MQTT session](https://www.hivemq.com/blog/mqtt-essentials-part-7-persistent-session-queuing-messages/)
on every MQTT connection.
<!--cerberus_section(depth=1)-->

- ### <small>_mqtt_.</small>`protocol`

```yaml
Type: string
Required: no
Default: 3.1.1
Allowed:
- '3.1'
- 3.1.1
```

Version of the MQTT protocol to use.

> This renders in the documentation as a float, but should always be set within quotes.
<!--cerberus_section(depth=1)-->

- ### <small>_mqtt_.</small>`keepalive`

```yaml
Type: integer
Required: no
Default: 10
Unit: seconds
Minimum value: 1
```

How frequently in seconds to send
[ping packets](https://www.hivemq.com/blog/mqtt-essentials-part-10-alive-client-take-over/)
to the MQTT server.
<!--cerberus_section(depth=1)-->

- ### <small>_mqtt_.</small>`status_topic`

```yaml
Type: string
Required: no
Default: status
```

Topic on which to send messages about the running status of this software.

> Sends the payloads configured in `status_payload_running`,
`status_payload_stopped` and `status_payload_dead`.
<!--cerberus_section(depth=1)-->

- ### <small>_mqtt_.</small>`status_payload_running`

```yaml
Type: string
Required: no
Default: running
```

Payload to send on the status topic when the software is running.
<!--cerberus_section(depth=1)-->

- ### <small>_mqtt_.</small>`status_payload_stopped`

```yaml
Type: string
Required: no
Default: stopped
```

Payload to send on the status topic when the software has exited cleanly.
<!--cerberus_section(depth=1)-->

- ### <small>_mqtt_.</small>`status_payload_dead`

```yaml
Type: string
Required: no
Default: dead
```

Payload to send on the status topic when the software has exited unexpectedly.

> Uses [MQTT Last Will and Testament](https://www.hivemq.com/blog/mqtt-essentials-part-9-last-will-and-testament/)
to make the server automatically send this payload if our connection fails.
<!--cerberus_section(depth=1)-->

- ### <small>_mqtt_.</small>`discovery`

```yaml
Type: boolean
Required: no
```

Enable [Home Assistant MQTT discovery](https://www.home-assistant.io/docs/mqtt/discovery/)
of our configured devices.
<!--cerberus_section(depth=1)-->

- ### <small>_mqtt_.</small>`discovery_prefix`

```yaml
Type: string
Required: no
Default: homeassistant
```

Prefix for the Home Assistant MQTT discovery topic.
<!--cerberus_section(depth=1)-->

- ### <small>_mqtt_.</small>`discovery_name`

```yaml
Type: string
Required: no
Default: MQTT IO
```

Name to identify this "device" in Home Assistant.
<!--cerberus_section(depth=1)-->

- ### <small>_mqtt_.</small>`client_module`

```yaml
Type: string
Required: no
Default: mqtt_io.mqtt.asyncio_mqtt
```

MQTT Client implementation module path.

> There's currently only one implementation, which uses the
[asyncio-mqtt](https://github.com/sbtinstruments/asyncio-mqtt/) client.
<!--cerberus_section(depth=1)-->

- ### <small>_mqtt_.</small>`tls`

-------------------

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

### Section options:
<!--schema_section(depth=2)-->
<!--cerberus_section(depth=2)-->

- - #### <small>_mqtt.tls_.</small>`enabled`

```yaml
Type: boolean
Required: yes
```

Enable a secure connection to the MQTT server.

> Most of these options map directly to the
[`tls_set()` arguments](https://www.eclipse.org/paho/index.php?page=clients/python/docs/index.php#tls-set)
on the Paho MQTT client.
<!--cerberus_section(depth=2)-->

- - #### <small>_mqtt.tls_.</small>`ca_certs`

```yaml
Type: string
Required: no
```

Path to the Certificate Authority certificate files that are to be treated
as trusted by this client.
[More info](https://www.eclipse.org/paho/index.php?page=clients/python/docs/index.php#tls-set)
<!--cerberus_section(depth=2)-->

- - #### <small>_mqtt.tls_.</small>`certfile`

```yaml
Type: string
Required: no
```

Path to the PEM encoded client certificate.
[More info](https://www.eclipse.org/paho/index.php?page=clients/python/docs/index.php#tls-set)
<!--cerberus_section(depth=2)-->

- - #### <small>_mqtt.tls_.</small>`keyfile`

```yaml
Type: string
Required: no
```

Path to the PEM encoded client private key.
[More info](https://www.eclipse.org/paho/index.php?page=clients/python/docs/index.php#tls-set)
<!--cerberus_section(depth=2)-->

- - #### <small>_mqtt.tls_.</small>`cert_reqs`

```yaml
Type: string
Required: no
Default: CERT_REQUIRED
Allowed:
- CERT_NONE
- CERT_OPTIONAL
- CERT_REQUIRED
```

Defines the certificate requirements that the client imposes on the MQTT server.
[More info](https://www.eclipse.org/paho/index.php?page=clients/python/docs/index.php#tls-set)

> By default this is `CERT_REQUIRED`, which means that the broker must provide a certificate.
<!--cerberus_section(depth=2)-->

- - #### <small>_mqtt.tls_.</small>`tls_version`

```yaml
Type: string
Required: no
```

Specifies the version of the SSL/TLS protocol to be used.
[More info](https://www.eclipse.org/paho/index.php?page=clients/python/docs/index.php#tls-set)

> By default the highest TLS version is detected.
<!--cerberus_section(depth=2)-->

- - #### <small>_mqtt.tls_.</small>`ciphers`

```yaml
Type: string
Required: no
```

Which encryption ciphers are allowable for this connection.
[More info](https://www.eclipse.org/paho/index.php?page=clients/python/docs/index.php#tls-set)
<!--cerberus_section(depth=2)-->

- - #### <small>_mqtt.tls_.</small>`insecure`

```yaml
Type: boolean
Required: no
```

Configure verification of the server hostname in the server certificate.
[More info](https://www.eclipse.org/paho/index.php?page=clients/python/docs/index.php#tls-insecure-set)

> If set to true, it is impossible to guarantee that the host you are
connecting to is not impersonating your server. This can be useful in
initial server testing, but makes it possible for a malicious third party
to impersonate your server through DNS spoofing, for example.
Do not use this function in a real system. Setting value to true means there
is no point using encryption.
<!--cerberus_section(depth=0)-->

## `gpio_modules`

-------------------

```yaml
Type: list
Required: no
```

List of GPIO modules to configure for use with inputs and/or outputs.

Each of the entries in this list should be a dict using the following variables.

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

### Section options:
<!--schema_section(depth=1)-->
<!--schema_section(depth=2)-->
<!--cerberus_section(depth=2)-->

- ### <small>_gpio_modules.*_.</small>`name`

```yaml
Type: string
Required: yes
```

Your name for this configuration of the module. Will be referred to by entries
in the `digital_inputs` and/or `digital_outputs` sections.
<!--cerberus_section(depth=2)-->

- ### <small>_gpio_modules.*_.</small>`module`

```yaml
Type: string
Required: yes
```

Name of the module in the code. This is listed in the README's
"Supported Hardware" section in brackets.
<!--cerberus_section(depth=2)-->

- ### <small>_gpio_modules.*_.</small>`cleanup`

```yaml
Type: boolean
Required: no
Default: true
```

Whether to run the module's `cleanup()` method on exit.
<!--cerberus_section(depth=0)-->

## `sensor_modules`

-------------------

```yaml
Type: list
Required: no
```

List of sensor modules to configure for use with sensor inputs.

Each of the entries in this list should be a dict using the following variables.

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

### Section options:
<!--schema_section(depth=1)-->
<!--schema_section(depth=2)-->
<!--cerberus_section(depth=2)-->

- ### <small>_sensor_modules.*_.</small>`name`

```yaml
Type: string
Required: yes
```

Your name for this configuration of the module. Will be referred to by entries
in the `sensor_inputs` section.
<!--cerberus_section(depth=2)-->

- ### <small>_sensor_modules.*_.</small>`module`

```yaml
Type: string
Required: yes
```

Name of the module in the code. This is listed in the README's
"Supported Hardware" section in brackets.
<!--cerberus_section(depth=2)-->

- ### <small>_sensor_modules.*_.</small>`cleanup`

```yaml
Type: boolean
Required: no
Default: true
```

Whether to run the module's `cleanup()` method on exit.
<!--cerberus_section(depth=0)-->

## `stream_modules`

-------------------

```yaml
Type: list
Required: no
```

List of stream modules to configure.

Each of the entries in this list should be a dict using the following variables.

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

### Section options:
<!--schema_section(depth=1)-->
<!--schema_section(depth=2)-->
<!--cerberus_section(depth=2)-->

- ### <small>_stream_modules.*_.</small>`name`

```yaml
Type: string
Required: yes
```

Your name for this configuration of the module. Will be used in the topic on
which the stream's data is published and the topic on which messages can be
sent for writing to the stream.
<!--cerberus_section(depth=2)-->

- ### <small>_stream_modules.*_.</small>`module`

```yaml
Type: string
Required: yes
```

Name of the module in the code. This is listed in the README's
"Supported Hardware" section in brackets.
<!--cerberus_section(depth=2)-->

- ### <small>_stream_modules.*_.</small>`cleanup`

```yaml
Type: boolean
Required: no
Default: true
```

Whether to run the module's `cleanup()` method on exit.
<!--cerberus_section(depth=2)-->

- ### <small>_stream_modules.*_.</small>`retain`

```yaml
Type: boolean
Required: no
```

Whether to set the `retain` flag on MQTT messages publishing data received
from the stream.
<!--cerberus_section(depth=2)-->

- ### <small>_stream_modules.*_.</small>`read_interval`

```yaml
Type: float
Required: no
Default: 60
Unit: seconds
Minimum value: 0.01
```

How long to wait between polling the stream for new data.
<!--cerberus_section(depth=2)-->

- ### <small>_stream_modules.*_.</small>`read`

```yaml
Type: boolean
Required: no
Default: true
```

Whether to poll this stream for incoming data and publish it on an MQTT topic.
<!--cerberus_section(depth=2)-->

- ### <small>_stream_modules.*_.</small>`write`

```yaml
Type: boolean
Required: no
Default: true
```

Whether to subscribe to MQTT messages on a topic and write messages received on it to the stream.
<!--cerberus_section(depth=0)-->

## `digital_inputs`

-------------------

```yaml
Type: list
Required: no
```

### Section options:
<!--schema_section(depth=1)-->
<!--schema_section(depth=2)-->
<!--cerberus_section(depth=2)-->

- ### <small>_digital_inputs.*_.</small>`name`

```yaml
Type: string
Required: yes
```
<!--cerberus_section(depth=2)-->

- ### <small>_digital_inputs.*_.</small>`module`

```yaml
Type: string
Required: yes
```
<!--cerberus_section(depth=2)-->

- ### <small>_digital_inputs.*_.</small>`pin`

```yaml
Type: ['string', 'integer']
Required: yes
```
<!--cerberus_section(depth=2)-->

- ### <small>_digital_inputs.*_.</small>`on_payload`

```yaml
Type: string
Required: no
Default: 'ON'
```
<!--cerberus_section(depth=2)-->

- ### <small>_digital_inputs.*_.</small>`off_payload`

```yaml
Type: string
Required: no
Default: 'OFF'
```
<!--cerberus_section(depth=2)-->

- ### <small>_digital_inputs.*_.</small>`inverted`

```yaml
Type: boolean
Required: no
```
<!--cerberus_section(depth=2)-->

- ### <small>_digital_inputs.*_.</small>`interrupt_payload`

```yaml
Type: string
Required: no
Default: INT
```
<!--cerberus_section(depth=2)-->

- ### <small>_digital_inputs.*_.</small>`pullup`

```yaml
Type: boolean
Required: no
```
<!--cerberus_section(depth=2)-->

- ### <small>_digital_inputs.*_.</small>`pulldown`

```yaml
Type: boolean
Required: no
```
<!--cerberus_section(depth=2)-->

- ### <small>_digital_inputs.*_.</small>`interrupt`

```yaml
Type: string
Required: no
Allowed:
- rising
- falling
- both
```
<!--cerberus_section(depth=2)-->

- ### <small>_digital_inputs.*_.</small>`interrupt_for`

```yaml
Type: list
Required: no
```
<!--cerberus_section(depth=2)-->

- ### <small>_digital_inputs.*_.</small>`bouncetime`

```yaml
Type: integer
Required: no
Default: 100
Minimum value: 1
```
<!--cerberus_section(depth=2)-->

- ### <small>_digital_inputs.*_.</small>`retain`

```yaml
Type: boolean
Required: no
```
<!--cerberus_section(depth=2)-->

- ### <small>_digital_inputs.*_.</small>`poll_interval`

```yaml
Type: float
Required: no
Default: 0.1
```
<!--cerberus_section(depth=2)-->

- ### <small>_digital_inputs.*_.</small>`poll_when_interrupt_for`

```yaml
Type: boolean
Required: no
Default: true
```
<!--cerberus_section(depth=2)-->

- ### <small>_digital_inputs.*_.</small>`ha_discovery`

-------------------

```yaml
Type: dict
Required: no
```

### Section options:
<!--schema_section(depth=3)-->
<!--cerberus_section(depth=3)-->

- - #### <small>_digital_inputs.*.ha_discovery_.</small>`component`

```yaml
Type: string
Required: no
Default: binary_sensor
```
<!--cerberus_section(depth=0)-->

## `digital_outputs`

-------------------

```yaml
Type: list
Required: no
```

### Section options:
<!--schema_section(depth=1)-->
<!--schema_section(depth=2)-->
<!--cerberus_section(depth=2)-->

- ### <small>_digital_outputs.*_.</small>`name`

```yaml
Type: string
Required: yes
```
<!--cerberus_section(depth=2)-->

- ### <small>_digital_outputs.*_.</small>`module`

```yaml
Type: string
Required: yes
```
<!--cerberus_section(depth=2)-->

- ### <small>_digital_outputs.*_.</small>`pin`

```yaml
Type: ['string', 'integer']
Required: yes
```
<!--cerberus_section(depth=2)-->

- ### <small>_digital_outputs.*_.</small>`on_payload`

```yaml
Type: string
Required: no
Default: 'ON'
```
<!--cerberus_section(depth=2)-->

- ### <small>_digital_outputs.*_.</small>`off_payload`

```yaml
Type: string
Required: no
Default: 'OFF'
```
<!--cerberus_section(depth=2)-->

- ### <small>_digital_outputs.*_.</small>`inverted`

```yaml
Type: boolean
Required: no
```
<!--cerberus_section(depth=2)-->

- ### <small>_digital_outputs.*_.</small>`timed_set_ms`

```yaml
Type: integer
Required: no
```
<!--cerberus_section(depth=2)-->

- ### <small>_digital_outputs.*_.</small>`initial`

```yaml
Type: string
Required: no
Allowed:
- high
- low
```
<!--cerberus_section(depth=2)-->

- ### <small>_digital_outputs.*_.</small>`publish_initial`

```yaml
Type: boolean
Required: no
```
<!--cerberus_section(depth=2)-->

- ### <small>_digital_outputs.*_.</small>`retain`

```yaml
Type: boolean
Required: no
```
<!--cerberus_section(depth=2)-->

- ### <small>_digital_outputs.*_.</small>`ha_discovery`

-------------------

```yaml
Type: dict
Required: no
```

### Section options:
<!--schema_section(depth=3)-->
<!--cerberus_section(depth=3)-->

- - #### <small>_digital_outputs.*.ha_discovery_.</small>`component`

```yaml
Type: string
Required: no
Default: switch
```
<!--cerberus_section(depth=0)-->

## `sensor_inputs`

-------------------

```yaml
Type: list
Required: no
```

### Section options:
<!--schema_section(depth=1)-->
<!--schema_section(depth=2)-->
<!--cerberus_section(depth=2)-->

- ### <small>_sensor_inputs.*_.</small>`name`

```yaml
Type: string
Required: yes
```
<!--cerberus_section(depth=2)-->

- ### <small>_sensor_inputs.*_.</small>`module`

```yaml
Type: string
Required: yes
```
<!--cerberus_section(depth=2)-->

- ### <small>_sensor_inputs.*_.</small>`retain`

```yaml
Type: boolean
Required: no
```
<!--cerberus_section(depth=2)-->

- ### <small>_sensor_inputs.*_.</small>`interval`

```yaml
Type: integer
Required: no
Default: 60
Minimum value: 1
```
<!--cerberus_section(depth=2)-->

- ### <small>_sensor_inputs.*_.</small>`digits`

```yaml
Type: integer
Required: no
Default: 2
```
<!--cerberus_section(depth=2)-->

- ### <small>_sensor_inputs.*_.</small>`unit_of_measurement`

```yaml
Type: string
Required: no
```
<!--cerberus_section(depth=2)-->

- ### <small>_sensor_inputs.*_.</small>`expire_after`

```yaml
Type: integer
Required: no
Minimum value: 1
```
<!--cerberus_section(depth=2)-->

- ### <small>_sensor_inputs.*_.</small>`ha_discovery`

-------------------

```yaml
Type: dict
Required: no
```

### Section options:
<!--schema_section(depth=3)-->
<!--cerberus_section(depth=3)-->

- - #### <small>_sensor_inputs.*.ha_discovery_.</small>`component`

```yaml
Type: string
Required: no
Default: sensor
```
<!--cerberus_section(depth=0)-->

## `logging`

```yaml
Type: dict
Required: no
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