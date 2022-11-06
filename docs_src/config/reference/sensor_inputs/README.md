# sensor_inputs :id=sensor_inputs

List of sensor inputs to configure.

```yaml
Type: list
Required: False
Default: []
```

?> Some modules require extra config entries, specified by the modules themselves.
Until the documentation is written for the individual modules, please refer to the
`MODULE_SCHEMA` values of the module's code in
[the repository](https://github.com/flyte/pi-mqtt-gpio/tree/feature/asyncio/mqtt_io/modules).
TODO: Link this to the pending wiki pages on each module's requirements.


**Example**:

```yaml
sensor_modules:
  - name: dht
    module: dht22
    type: AM2302
    pin: 4

  - name: ds
    module: ds18b
    type: DS18B20
    address: 000803702e49

sensor_inputs:
  - name: workshop_temp
    module: dht
    type: temperature
    interval: 30

  - name: workshop_humidity
    module: dht
    type: humidity
    interval: 60

  - name: outdoor_temp
    module: ds
```

## sensor_inputs.* :id=sensor_inputs-star

*sensor_inputs*.**&ast;**

```yaml
Type: dict
Required: 
Unlisted entries accepted: True
```

## name :id=sensor_inputs-star-name

*sensor_inputs.&ast;*.**name**

Name of the sensor. Used in the MQTT topic when publishing sensor values.

The topic that sensor values will be published to is:
`<mqtt.topic_prefix>/sensor/<this name>`


```yaml
Type: string
Required: True
```

## module :id=sensor_inputs-star-module

*sensor_inputs.&ast;*.**module**

Name of the module configured in `sensor_modules` that this sensor reading
comes from.


```yaml
Type: string
Required: True
```

## retain :id=sensor_inputs-star-retain

*sensor_inputs.&ast;*.**retain**

Set the retain flag on MQTT messages published on sensor read.

```yaml
Type: boolean
Required: False
Default: False
```

## interval :id=sensor_inputs-star-interval

*sensor_inputs.&ast;*.**interval**

How long to wait between checking the value of this sensor.

```yaml
Type: integer
Required: False
Unit: seconds
Default: 60
```

## digits :id=sensor_inputs-star-digits

*sensor_inputs.&ast;*.**digits**

How many decimal places to round the sensor reading to.

```yaml
Type: integer
Required: False
Default: 2
```

## ha_discovery :id=sensor_inputs-star-ha_discovery

*sensor_inputs.&ast;*.**ha_discovery**

Configures the
[Home Assistant MQTT discovery](https://www.home-assistant.io/docs/mqtt/discovery/)
for this sensor.

Any values entered into this section will be sent as part of the discovery
config payload. See the above link for documentation.


```yaml
Type: dict
Required: 
Unlisted entries accepted: True
```

**Example**:

```yaml
sensor_inputs:
  - name: workshop_temp
    module: dht
    type: temperature
    ha_discovery:
      name: Workshop Temperature
      device_class: temperature
      unit_of_measurement: °C

  - name: workshop_humidity
    module: dht
    type: humidity
    ha_discovery:
      name: Workshop Humidity
      device_class: humidity
      unit_of_measurement: %
```

### component :id=sensor_inputs-star-ha_discovery-component

*sensor_inputs.&ast;.ha_discovery*.**component**

Type of component to report this sensor as to Home Assistant.

```yaml
Type: string
Required: False
Default: sensor
```

### expire_after :id=sensor_inputs-star-ha_discovery-expire_after

*sensor_inputs.&ast;.ha_discovery*.**expire_after**

How long after receiving a sensor update to declare it invalid.

```yaml
Type: integer
Required: False
```

?> Defaults to `interval` * 2 + 5


