# digital_outputs :id=digital_outputs

List of digital outputs to configure.

```yaml
Type: list
Required: False
Default: []
```

?> Some modules require extra config entries, specified by the modules themselves.
Until the documentation is written for the individual modules, please refer to the
`PIN_SCHEMA` and `OUTPUT_SCHEMA` values of the module's code in
[the repository](https://github.com/flyte/pi-mqtt-gpio/tree/feature/asyncio/mqtt_io/modules).
TODO: Link this to the pending wiki pages on each module's requirements.


**Example**:

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

## digital_outputs.* :id=digital_outputs-star

*digital_outputs*.**&ast;**

```yaml
Type: dict
Required: 
Unlisted entries accepted: True
```

## name :id=digital_outputs-star-name

*digital_outputs.&ast;*.**name**

Name of the output. Used in the MQTT topics that are subscribed to in order to
change the output value according to received MQTT messages, as well as in the
MQTT topic for publishing output changes.

The topics subscribed to for each output are:
- `<mqtt.topic_prefix>/output/<this name>/set`
- `<mqtt.topic_prefix>/output/<this name>/set_on_ms`
- `<mqtt.topic_prefix>/output/<this name>/set_off_ms`

The topic that output changes will be published to is:
`<mqtt.topic_prefix>/output/<this name>`


```yaml
Type: string
Required: True
```

## module :id=digital_outputs-star-module

*digital_outputs.&ast;*.**module**

Name of the module configured in `gpio_modules` that this output is attached to.


```yaml
Type: string
Required: True
```

## pin :id=digital_outputs-star-pin

*digital_outputs.&ast;*.**pin**

Which of the GPIO module's pins this output refers to.

```yaml
Type: ['string', 'integer']
Required: True
```

?> Depending on the GPIO module's implementation, this can be either a string
or an integer.


## on_payload :id=digital_outputs-star-on_payload

*digital_outputs.&ast;*.**on_payload**

Payload to consider as "on" when received to the `/set` topic for this output.
See `inverted` below for the definition of "on" and "off".


```yaml
Type: string
Required: False
Default: ON
```

?> Make sure to avoid YAML's automatic boolean type conversion when setting this
option by surrounding potential booleans with quotes.
See the "Regexp" section of the
[YAML bool docs](https://yaml.org/type/bool.html) for all of the values that
will be parsed as boolean.


## off_payload :id=digital_outputs-star-off_payload

*digital_outputs.&ast;*.**off_payload**

Payload to consider as "off" when received to the `/set` topic for this output.
See `inverted` below for the definition of "on" and "off".


```yaml
Type: string
Required: False
Default: OFF
```

?> Make sure to avoid YAML's automatic boolean type conversion when setting this
option by surrounding potential booleans with quotes.
See the "Regexp" section of the
[YAML bool docs](https://yaml.org/type/bool.html) for all of the values that
will be parsed as boolean.


## inverted :id=digital_outputs-star-inverted

*digital_outputs.&ast;*.**inverted**

Invert the logic level so that "low" levels are considered to be "on" and
"high" levels are considered "off".


```yaml
Type: boolean
Required: False
Default: False
```

?> This can be useful for when an output turns something on when its output is
"low".


## timed_set_ms :id=digital_outputs-star-timed_set_ms

*digital_outputs.&ast;*.**timed_set_ms**

How long to set an output to the desired value on receipt of an MQTT message
to the `/set` topic before then setting it back to the opposite value.


```yaml
Type: integer
Required: False
Unit: milliseconds
```

?> This may be useful if the output controls a device where leaving the ouput
"on" for too long would be detrimental. Using this option means that you don't
have to rely on a second "off" message getting through MQTT for the output to
return to a safe state.


## initial :id=digital_outputs-star-initial

*digital_outputs.&ast;*.**initial**

Set the output to an initial "high" or "low" state when the software starts.


```yaml
Type: string
Required: False
Allowed: ['high', 'low']
```

## publish_initial :id=digital_outputs-star-publish_initial

*digital_outputs.&ast;*.**publish_initial**

Whether to publish an MQTT message for the initial "high" or "low" state set
above.


```yaml
Type: boolean
Required: False
Default: False
```

## retain :id=digital_outputs-star-retain

*digital_outputs.&ast;*.**retain**

Set the retain flag on MQTT messages published on output change.

```yaml
Type: boolean
Required: False
Default: False
```

## ha_discovery :id=digital_outputs-star-ha_discovery

*digital_outputs.&ast;*.**ha_discovery**

Configures the
[Home Assistant MQTT discovery](https://www.home-assistant.io/docs/mqtt/discovery/)
for this pin.

Any values entered into this section will be sent as part of the discovery
config payload. See the above link for documentation.


```yaml
Type: dict
Required: 
Unlisted entries accepted: True
```

**Example**:

```yaml
digital_outputs:
  - name: garage_door1
    module: rpi
    ha_discovery:
      component: switch
      name: Ferrari Garage Door
      device_class: garage_door
```

### component :id=digital_outputs-star-ha_discovery-component

*digital_outputs.&ast;.ha_discovery*.**component**

Type of component to report this output as to Home Assistant.

```yaml
Type: string
Required: False
Default: switch
```

