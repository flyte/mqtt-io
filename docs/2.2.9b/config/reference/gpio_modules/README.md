# gpio_modules :id=gpio_modules

List of GPIO modules to configure for use with inputs and/or outputs.


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
gpio_modules:
  - name: rpi_gpio
    module: raspberrypi
  
  - name: pcf
    module: pcf8574
    i2c_bus_num: 1
    chip_addr: 0x20
```

## gpio_modules.* :id=gpio_modules-star

*gpio_modules*.**&ast;**

```yaml
Type: dict
Required: 
Unlisted entries accepted: True
```

## name :id=gpio_modules-star-name

*gpio_modules.&ast;*.**name**

Your name for this configuration of the module. Will be referred to by entries
in the `digital_inputs` and/or `digital_outputs` sections.


```yaml
Type: string
Required: True
```

## module :id=gpio_modules-star-module

*gpio_modules.&ast;*.**module**

Name of the module in the code. This is listed in the README's
"Supported Hardware" section in brackets.


```yaml
Type: string
Required: True
```

## cleanup :id=gpio_modules-star-cleanup

*gpio_modules.&ast;*.**cleanup**

Whether to run the module's `cleanup()` method on exit.

```yaml
Type: boolean
Required: False
Default: True
```

