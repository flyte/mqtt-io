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
<!--schema_section(depth=2)-->
<!--cerberus_section(depth=2)-->

- - #### <small>_mqtt.tls_.</small>`enabled`

```yaml
Type: boolean
Required: yes
```
<!--cerberus_section(depth=2)-->

- - #### <small>_mqtt.tls_.</small>`ca_certs`

```yaml
Type: string
Required: no
```
<!--cerberus_section(depth=2)-->

- - #### <small>_mqtt.tls_.</small>`certfile`

```yaml
Type: string
Required: no
```
<!--cerberus_section(depth=2)-->

- - #### <small>_mqtt.tls_.</small>`keyfile`

```yaml
Type: string
Required: no
```
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
<!--cerberus_section(depth=2)-->

- - #### <small>_mqtt.tls_.</small>`tls_version`

```yaml
Type: string
Required: no
```
<!--cerberus_section(depth=2)-->

- - #### <small>_mqtt.tls_.</small>`ciphers`

```yaml
Type: string
Required: no
```
<!--cerberus_section(depth=2)-->

- - #### <small>_mqtt.tls_.</small>`insecure`

```yaml
Type: boolean
Required: no
```
<!--cerberus_section(depth=0)-->

## `gpio_modules`

-------------------

```yaml
Type: list
Required: no
```
<!--schema_section(depth=1)-->
<!--schema_section(depth=1)-->
<!--cerberus_section(depth=1)-->

- ### <small>_gpio_modules_.</small>`name`

```yaml
Type: string
Required: yes
```
<!--cerberus_section(depth=1)-->

- ### <small>_gpio_modules_.</small>`module`

```yaml
Type: string
Required: yes
```
<!--cerberus_section(depth=1)-->

- ### <small>_gpio_modules_.</small>`cleanup`

```yaml
Type: boolean
Required: no
Default: true
```
<!--cerberus_section(depth=0)-->

## `sensor_modules`

-------------------

```yaml
Type: list
Required: no
```
<!--schema_section(depth=1)-->
<!--schema_section(depth=1)-->
<!--cerberus_section(depth=1)-->

- ### <small>_sensor_modules_.</small>`name`

```yaml
Type: string
Required: yes
```
<!--cerberus_section(depth=1)-->

- ### <small>_sensor_modules_.</small>`module`

```yaml
Type: string
Required: yes
```
<!--cerberus_section(depth=1)-->

- ### <small>_sensor_modules_.</small>`cleanup`

```yaml
Type: boolean
Required: no
Default: true
```
<!--cerberus_section(depth=0)-->

## `stream_modules`

-------------------

```yaml
Type: list
Required: no
```
<!--schema_section(depth=1)-->
<!--schema_section(depth=1)-->
<!--cerberus_section(depth=1)-->

- ### <small>_stream_modules_.</small>`name`

```yaml
Type: string
Required: yes
```
<!--cerberus_section(depth=1)-->

- ### <small>_stream_modules_.</small>`module`

```yaml
Type: string
Required: yes
```
<!--cerberus_section(depth=1)-->

- ### <small>_stream_modules_.</small>`cleanup`

```yaml
Type: boolean
Required: no
Default: true
```
<!--cerberus_section(depth=1)-->

- ### <small>_stream_modules_.</small>`retain`

```yaml
Type: boolean
Required: no
```
<!--cerberus_section(depth=1)-->

- ### <small>_stream_modules_.</small>`read_interval`

```yaml
Type: float
Required: no
Default: 60
Minimum value: 0.01
```
<!--cerberus_section(depth=1)-->

- ### <small>_stream_modules_.</small>`read`

```yaml
Type: boolean
Required: no
Default: true
```
<!--cerberus_section(depth=1)-->

- ### <small>_stream_modules_.</small>`write`

```yaml
Type: boolean
Required: no
Default: true
```
<!--cerberus_section(depth=0)-->

## `digital_inputs`

-------------------

```yaml
Type: list
Required: no
```
<!--schema_section(depth=1)-->
<!--schema_section(depth=1)-->
<!--cerberus_section(depth=1)-->

- ### <small>_digital_inputs_.</small>`name`

```yaml
Type: string
Required: yes
```
<!--cerberus_section(depth=1)-->

- ### <small>_digital_inputs_.</small>`module`

```yaml
Type: string
Required: yes
```
<!--cerberus_section(depth=1)-->

- ### <small>_digital_inputs_.</small>`pin`

```yaml
Type: ['string', 'integer']
Required: yes
```
<!--cerberus_section(depth=1)-->

- ### <small>_digital_inputs_.</small>`on_payload`

```yaml
Type: string
Required: no
Default: 'ON'
```
<!--cerberus_section(depth=1)-->

- ### <small>_digital_inputs_.</small>`off_payload`

```yaml
Type: string
Required: no
Default: 'OFF'
```
<!--cerberus_section(depth=1)-->

- ### <small>_digital_inputs_.</small>`inverted`

```yaml
Type: boolean
Required: no
```
<!--cerberus_section(depth=1)-->

- ### <small>_digital_inputs_.</small>`interrupt_payload`

```yaml
Type: string
Required: no
Default: INT
```
<!--cerberus_section(depth=1)-->

- ### <small>_digital_inputs_.</small>`pullup`

```yaml
Type: boolean
Required: no
```
<!--cerberus_section(depth=1)-->

- ### <small>_digital_inputs_.</small>`pulldown`

```yaml
Type: boolean
Required: no
```
<!--cerberus_section(depth=1)-->

- ### <small>_digital_inputs_.</small>`interrupt`

```yaml
Type: string
Required: no
Allowed:
- rising
- falling
- both
```
<!--cerberus_section(depth=1)-->

- ### <small>_digital_inputs_.</small>`interrupt_for`

```yaml
Type: list
Required: no
```
<!--cerberus_section(depth=1)-->

- ### <small>_digital_inputs_.</small>`bouncetime`

```yaml
Type: integer
Required: no
Default: 100
Minimum value: 1
```
<!--cerberus_section(depth=1)-->

- ### <small>_digital_inputs_.</small>`retain`

```yaml
Type: boolean
Required: no
```
<!--cerberus_section(depth=1)-->

- ### <small>_digital_inputs_.</small>`poll_interval`

```yaml
Type: float
Required: no
Default: 0.1
```
<!--cerberus_section(depth=1)-->

- ### <small>_digital_inputs_.</small>`poll_when_interrupt_for`

```yaml
Type: boolean
Required: no
Default: true
```
<!--cerberus_section(depth=1)-->

- ### <small>_digital_inputs_.</small>`ha_discovery`

-------------------

```yaml
Type: dict
Required: no
```
<!--schema_section(depth=2)-->
<!--cerberus_section(depth=2)-->

- - #### <small>_digital_inputs.ha_discovery_.</small>`component`

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
<!--schema_section(depth=1)-->
<!--schema_section(depth=1)-->
<!--cerberus_section(depth=1)-->

- ### <small>_digital_outputs_.</small>`name`

```yaml
Type: string
Required: yes
```
<!--cerberus_section(depth=1)-->

- ### <small>_digital_outputs_.</small>`module`

```yaml
Type: string
Required: yes
```
<!--cerberus_section(depth=1)-->

- ### <small>_digital_outputs_.</small>`pin`

```yaml
Type: ['string', 'integer']
Required: yes
```
<!--cerberus_section(depth=1)-->

- ### <small>_digital_outputs_.</small>`on_payload`

```yaml
Type: string
Required: no
Default: 'ON'
```
<!--cerberus_section(depth=1)-->

- ### <small>_digital_outputs_.</small>`off_payload`

```yaml
Type: string
Required: no
Default: 'OFF'
```
<!--cerberus_section(depth=1)-->

- ### <small>_digital_outputs_.</small>`inverted`

```yaml
Type: boolean
Required: no
```
<!--cerberus_section(depth=1)-->

- ### <small>_digital_outputs_.</small>`timed_set_ms`

```yaml
Type: integer
Required: no
```
<!--cerberus_section(depth=1)-->

- ### <small>_digital_outputs_.</small>`initial`

```yaml
Type: string
Required: no
Allowed:
- high
- low
```
<!--cerberus_section(depth=1)-->

- ### <small>_digital_outputs_.</small>`publish_initial`

```yaml
Type: boolean
Required: no
```
<!--cerberus_section(depth=1)-->

- ### <small>_digital_outputs_.</small>`retain`

```yaml
Type: boolean
Required: no
```
<!--cerberus_section(depth=1)-->

- ### <small>_digital_outputs_.</small>`ha_discovery`

-------------------

```yaml
Type: dict
Required: no
```
<!--schema_section(depth=2)-->
<!--cerberus_section(depth=2)-->

- - #### <small>_digital_outputs.ha_discovery_.</small>`component`

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
<!--schema_section(depth=1)-->
<!--schema_section(depth=1)-->
<!--cerberus_section(depth=1)-->

- ### <small>_sensor_inputs_.</small>`name`

```yaml
Type: string
Required: yes
```
<!--cerberus_section(depth=1)-->

- ### <small>_sensor_inputs_.</small>`module`

```yaml
Type: string
Required: yes
```
<!--cerberus_section(depth=1)-->

- ### <small>_sensor_inputs_.</small>`retain`

```yaml
Type: boolean
Required: no
```
<!--cerberus_section(depth=1)-->

- ### <small>_sensor_inputs_.</small>`interval`

```yaml
Type: integer
Required: no
Default: 60
Minimum value: 1
```
<!--cerberus_section(depth=1)-->

- ### <small>_sensor_inputs_.</small>`digits`

```yaml
Type: integer
Required: no
Default: 2
```
<!--cerberus_section(depth=1)-->

- ### <small>_sensor_inputs_.</small>`unit_of_measurement`

```yaml
Type: string
Required: no
```
<!--cerberus_section(depth=1)-->

- ### <small>_sensor_inputs_.</small>`expire_after`

```yaml
Type: integer
Required: no
Minimum value: 1
```
<!--cerberus_section(depth=1)-->

- ### <small>_sensor_inputs_.</small>`ha_discovery`

-------------------

```yaml
Type: dict
Required: no
```
<!--schema_section(depth=2)-->
<!--cerberus_section(depth=2)-->

- - #### <small>_sensor_inputs.ha_discovery_.</small>`component`

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