# sensor_modules :id=sensor_modules

List of sensor modules to configure for use with sensor inputs.

```yaml
Type: list
Required: False
Default: []
```

?> Some modules require extra config entries, specified by the modules themselves.
Until the documentation is written for the individual modules, please refer to the
`CONFIG_SCHEMA` value of the module's code in
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
    type: DS18S20
    address: 000803702e49
```

## sensor_modules.* :id=sensor_modules-star

*sensor_modules*.**&ast;**

```yaml
Type: dict
Required: 
Unlisted entries accepted: True
```

## name :id=sensor_modules-star-name

*sensor_modules.&ast;*.**name**

Your name for this configuration of the module. Will be referred to by entries
in the `sensor_inputs` section.


```yaml
Type: string
Required: True
```

## module :id=sensor_modules-star-module

*sensor_modules.&ast;*.**module**

Name of the module in the code. This is listed in the README's
"Supported Hardware" section in brackets.


```yaml
Type: string
Required: True
```

## cleanup :id=sensor_modules-star-cleanup

*sensor_modules.&ast;*.**cleanup**

Whether to run the module's `cleanup()` method on exit.

```yaml
Type: boolean
Required: False
Default: True
```

