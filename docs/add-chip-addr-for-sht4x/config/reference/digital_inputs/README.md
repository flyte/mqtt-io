# digital_inputs :id=digital_inputs

List of digital inputs to configure.

```yaml
Type: list
Required: False
Default: []
```

?> Some modules require extra config entries, specified by the modules themselves.
Until the documentation is written for the individual modules, please refer to the
`PIN_SCHEMA` and `INPUT_SCHEMA` values of the module's code in
[the repository](https://github.com/flyte/pi-mqtt-gpio/tree/feature/asyncio/mqtt_io/modules).
TODO: Link this to the pending wiki pages on each module's requirements.


**Example**:

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

## digital_inputs.* :id=digital_inputs-star

*digital_inputs*.**&ast;**

```yaml
Type: dict
Required: 
Unlisted entries accepted: True
```

## name :id=digital_inputs-star-name

*digital_inputs.&ast;*.**name**

Name of the input. Used in the MQTT topic when publishing input changes.

The topic that input changes will be published to is:
`<mqtt.topic_prefix>/input/<this name>`


```yaml
Type: string
Required: True
```

## module :id=digital_inputs-star-module

*digital_inputs.&ast;*.**module**

Name of the module configured in `gpio_modules` that this input is attached to.


```yaml
Type: string
Required: True
```

## pin :id=digital_inputs-star-pin

*digital_inputs.&ast;*.**pin**

Which of the GPIO module's pins this input refers to.

```yaml
Type: ['string', 'integer']
Required: True
```

?> Depending on the GPIO module's implementation, this can be either a string
or an integer.


## on_payload :id=digital_inputs-star-on_payload

*digital_inputs.&ast;*.**on_payload**

Payload to be sent when the input changes to what is considered to be "on".
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


## off_payload :id=digital_inputs-star-off_payload

*digital_inputs.&ast;*.**off_payload**

Payload to be sent when the input changes to what is considered to be "off".
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


## inverted :id=digital_inputs-star-inverted

*digital_inputs.&ast;*.**inverted**

Invert the logic level so that "low" levels are considered to be "on" and
"high" levels are considered "off".


```yaml
Type: boolean
Required: False
Default: False
```

?> This can be useful for when an input is pulled "high" with a resistor and a
device (like a button or another IC) connects it to ground when it's "active".


## pullup :id=digital_inputs-star-pullup

*digital_inputs.&ast;*.**pullup**

Enable the pull-up resistor for this input so that the logic level is pulled
"high" by default.


```yaml
Type: boolean
Required: False
Default: False
```

?> Not all GPIO modules support pull-up resistors.

## pulldown :id=digital_inputs-star-pulldown

*digital_inputs.&ast;*.**pulldown**

Enable the pull-down resistor for this input so that the logic level is pulled
"low" by default.


```yaml
Type: boolean
Required: False
Default: False
```

?> Not all GPIO modules support pull-down resistors.

## interrupt :id=digital_inputs-star-interrupt

*digital_inputs.&ast;*.**interrupt**

Configure this pin to trigger an interrupt when the logic level is "rising",
"falling" or "both".


```yaml
Type: string
Required: False
Allowed: ['rising', 'falling', 'both']
```

?> Not all GPIO modules support interrupts, and those that do may do so in
various ways.
TODO: Add link to interrupt documentation.


## interrupt_for :id=digital_inputs-star-interrupt_for

*digital_inputs.&ast;*.**interrupt_for**

List of other pin names that this pin is an interrupt for.

This is generally used on GPIO modules that provide software callbacks on
interrupts, so that we can attach another "remote" module's interrupt output
pin (one that changes logic level when one of its pins triggers an interrupt)
to this input and use the callback to get the value of the "remote" pin and
publish it on MQTT.

TODO: Add link to interrupt documentation.


```yaml
Type: list
Required: False
```

### interrupt_for.* :id=digital_inputs-star-interrupt_for-star

*digital_inputs.&ast;.interrupt_for*.**&ast;**

```yaml
Type: string
Required: True
```

## bouncetime :id=digital_inputs-star-bouncetime

*digital_inputs.&ast;*.**bouncetime**

Don't trigger interrupts more frequently than once per `bouncetime`.


```yaml
Type: integer
Required: False
Unit: milliseconds
Default: 100
```

## retain :id=digital_inputs-star-retain

*digital_inputs.&ast;*.**retain**

Set the retain flag on MQTT messages published on input change.

```yaml
Type: boolean
Required: False
Default: False
```

## poll_interval :id=digital_inputs-star-poll_interval

*digital_inputs.&ast;*.**poll_interval**

How long to wait between checking the value of this input.

```yaml
Type: float
Required: False
Unit: seconds
Default: 0.1
```

?> When the pin is configured as an interrupt, the pin is no longer polled.
The only exception to this is if the pin is configured as an interrupt for
another pin. In this case, whether or not we poll is decided by the
`poll_when_interrupt_for` setting below.


## poll_when_interrupt_for :id=digital_inputs-star-poll_when_interrupt_for

*digital_inputs.&ast;*.**poll_when_interrupt_for**

Poll this pin when it's configured as an interrupt for another pin.

```yaml
Type: boolean
Required: False
Default: True
```

?> Polling the pin when it's configured as an interrupt for another pin is useful
in order to make sure that if we somehow miss an interrupt on this pin (the
remote module's interrupt output pin goes low ("triggered")), we
don't end up stuck in that state where we don't handle the remote module's
interrupt at all. If we poll the "triggered" value on this pin and our
interrupt handling hasn't dealt with it, then we'll handle it here.


## ha_discovery :id=digital_inputs-star-ha_discovery

*digital_inputs.&ast;*.**ha_discovery**

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
digital_inputs:
  - name: livingroom_motion
    module: rpi
    ha_discovery:
      component: binary_sensor
      name: Living Room Motion
      device_class: motion
```

### component :id=digital_inputs-star-ha_discovery-component

*digital_inputs.&ast;.ha_discovery*.**component**

Type of component to report this input as to Home Assistant.

```yaml
Type: string
Required: False
Default: binary_sensor
```

