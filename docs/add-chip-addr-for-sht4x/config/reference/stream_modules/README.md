# stream_modules :id=stream_modules

List of stream modules to configure.

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

## stream_modules.* :id=stream_modules-star

*stream_modules*.**&ast;**

```yaml
Type: dict
Required: 
Unlisted entries accepted: True
```

## name :id=stream_modules-star-name

*stream_modules.&ast;*.**name**

Your name for this configuration of the module. Will be used in the topic on
which the stream's data is published and the topic on which messages can be
sent for writing to the stream.


```yaml
Type: string
Required: True
```

## module :id=stream_modules-star-module

*stream_modules.&ast;*.**module**

Name of the module in the code. This is listed in the README's
"Supported Hardware" section in brackets.


```yaml
Type: string
Required: True
```

## cleanup :id=stream_modules-star-cleanup

*stream_modules.&ast;*.**cleanup**

Whether to run the module's `cleanup()` method on exit.

```yaml
Type: boolean
Required: False
Default: True
```

## retain :id=stream_modules-star-retain

*stream_modules.&ast;*.**retain**

Whether to set the `retain` flag on MQTT messages publishing data received
from the stream.


```yaml
Type: boolean
Required: False
Default: False
```

## read_interval :id=stream_modules-star-read_interval

*stream_modules.&ast;*.**read_interval**

How long to wait between polling the stream for new data.

```yaml
Type: float
Required: False
Unit: seconds
Default: 60
```

## read :id=stream_modules-star-read

*stream_modules.&ast;*.**read**

Whether to poll this stream for incoming data and publish it on an MQTT topic.


```yaml
Type: boolean
Required: False
Default: True
```

## write :id=stream_modules-star-write

*stream_modules.&ast;*.**write**

Whether to subscribe to MQTT messages on a topic and write messages received on it to the stream.

```yaml
Type: boolean
Required: False
Default: True
```

