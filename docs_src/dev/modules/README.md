# Hardware Support Modules

In order to support as much hardware as possible without changing the project's core code, every supported piece of hardware will have a relevant GPIO, sensor or stream module. These reside in `mqtt_io/modules` within the `gpio`, `sensor` and `stream` folders respectively. In each of these folders is an `__init__.py` file which contains the base class for each type of module. The hardware modules must include a class which overrides this base class and is named `GPIO`, `Sensor` or `Stream`.

## Requirements

In order for a module to specify its requirements, a module-level constant is used which lists them in the same format as the `pip install` command.

[mqtt_io.modules.gpio.raspberrypi:REQUIREMENTS](https://github.com/flyte/mqtt-io/blob/develop/mqtt_io/modules/gpio/raspberrypi.py#L13):

```python
REQUIREMENTS = ("RPi.GPIO",)
```

## Config Schema

Along with the base module schema in `mqtt_io/config/config.schema.yml`, each hardware support module is able to specify extra config schema to allow the user to provide the details needed for using the specific hardware.

To specify extra schema for the module-level config sections (`gpio_modules`, `sensor_modules`, `stream_modules`), a _module-level_ constant called `CONFIG_SCHEMA` is set, containing the [Cerberus Schema](https://docs.python-cerberus.org/en/stable/schemas.html) to add to the base schema.

To specify extra schema for the pin-level config sections (`digital_inputs`, `digital_outputs`, `sensor_inputs` etc.), a _class-level_ constant called `PIN_SCHEMA` is set on the module's main class (`GPIO`, `Sensor`, `Stream`), containing the [Cerberus Schema](https://docs.python-cerberus.org/en/stable/schemas.html) to add to the base schema.

If the pin-level schema only applies to an input or an output (in the case of a GPIO module), then instead of setting it on the `PIN_SCHEMA` class-level constant, use `INPUT_SCHEMA` or `OUTPUT_SCHEMA` respectively.

[mqtt_io.modules.gpio.gpiod:CONFIG_SCHEMA](https://github.com/flyte/mqtt-io/blob/develop/mqtt_io/modules/gpio/gpiod.py#L18):

```python
CONFIG_SCHEMA = {
    "chip": {"type": "string", "required": False, "default": "/dev/gpiochip0"}
}
```

## GPIO Modules

...

### Lifecycle

#### `setup_module()`

During software startup, each GPIO module's `setup_module()` method will be called once per instance of the module in the `gpio_modules` section of the config file.

[mqtt_io.modules.gpio:GenericGPIO.setup_module](https://github.com/flyte/mqtt-io/blob/develop/mqtt_io/modules/gpio/__init__.py#L108):

```python
def setup_module(self) -> None:
    """
    Called on initialisation of the GPIO module during the startup phase.

    The module's config from the `gpio_modules` section of the config file is stored
    in `self.config`.
    """
```

For example, the `pcf8574` module's `setup_module()` method will be called twice given the following config:

```yaml
gpio_modules:
  - name: pcf1
    module: pcf8574
    i2c_bus_num: 1
    chip_addr: 0x20

  - name: pcf2
    module: pcf8574
    i2c_bus_num: 1
    chip_addr: 0x21
```

Within this method we import any Python dependencies. It's important to not do this at module level, so that the core code is able to import the module before its dependencies are installed.

The GPIO library is then initialised and an object may be stored (usually at `self.io`) for use by the module during runtime.

It may be appropriate to build mappings of pin directions (input, output), pullups (up, down, off) and interrupt edges (rising, falling, both) if appropriate for this hardware. The base GenericGPIO class uses its own constants to refer to these, so the mappings translate the base GenericGPIO's constants to ones used by the hardware's Python library.

[mqtt_io.modules.gpio:PinDirection](https://github.com/flyte/mqtt-io/blob/develop/mqtt_io/modules/gpio/__init__.py#L22):

```python
class PinDirection(Enum):
    """
    Whether the GPIO pin is an input or an output.
    """

    INPUT = auto()
    OUTPUT = auto()
```

[mqtt_io.modules.gpio:PinPUD](https://github.com/flyte/mqtt-io/blob/develop/mqtt_io/modules/gpio/__init__.py#L31):

```python
class PinPUD(Enum):
    """
    Whether the GPIO pin should be pulled up, down or not anywhere.
    """

    OFF = auto()
    UP = auto()
    DOWN = auto()
```

[mqtt_io.modules.gpio:InterruptEdge](https://github.com/flyte/mqtt-io/blob/develop/mqtt_io/modules/gpio/__init__.py#L41):

```python
class InterruptEdge(Enum):
    """
    Whether to trigger an interrupt on rising edge, falling edge or both.
    """

    RISING = auto()
    FALLING = auto()
    BOTH = auto()
```

The `raspberrypi` GPIO module is a good example of the above:

[mqtt_io.modules.gpio.raspberrypi:GPIO.setup_module](https://github.com/flyte/mqtt-io/blob/develop/mqtt_io/modules/gpio/raspberrypi.py#L23):

```python
def setup_module(self) -> None:
    # pylint: disable=import-outside-toplevel,import-error
    import RPi.GPIO as gpio  # type: ignore

    self.io = gpio
    self.direction_map = {PinDirection.INPUT: gpio.IN, PinDirection.OUTPUT: gpio.OUT}

    self.pullup_map = {
        PinPUD.OFF: gpio.PUD_OFF,
        PinPUD.UP: gpio.PUD_UP,
        PinPUD.DOWN: gpio.PUD_DOWN,
    }

    self.interrupt_edge_map = {
        InterruptEdge.RISING: gpio.RISING,
        InterruptEdge.FALLING: gpio.FALLING,
        InterruptEdge.BOTH: gpio.BOTH,
    }

    gpio.setmode(gpio.BCM)
```

#### Polling Loop

If a digital input is not configured as an [interrupt](config/interrupts.md) (or even [sometimes if it is](config/reference/digital_inputs/?id=digital_inputs-star-interrupt_for)), then a loop will be created which polls the pin's current value and publishes a `DigitalInputChangedEvent` event when it does. As part of the initialisation of each pin, a callback function to publish the new value on MQTT will be subscribed to this event.

[mqtt_io.server.MqttIo._init_digital_inputs](https://github.com/flyte/mqtt-io/blob/develop/mqtt_io/server.py#L344):

```python
def _init_digital_inputs(self) -> None:
    async def publish_callback(event: DigitalInputChangedEvent) -> None:
        in_conf = self.digital_input_configs[event.input_name]
        value = event.to_value != in_conf["inverted"]
        val = in_conf["on_payload"] if value else in_conf["off_payload"]
        self.mqtt_task_queue.put_nowait(
            PriorityCoro(
                self._mqtt_publish(
                    MQTTMessageSend(
                        "/".join(
                            (
                                self.config["mqtt"]["topic_prefix"],
                                INPUT_TOPIC,
                                event.input_name,
                            )
                        ),
                        val.encode("utf8"),
                        retain=in_conf["retain"],
                    )
                ),
                MQTT_PUB_PRIORITY,
            )
        )
    self.event_bus.subscribe(DigitalInputChangedEvent, publish_callback)
```

#### `setup_pin()`

For each of the entries in `digital_inputs` and `digital_outputs`, `setup_pin()` will be called. This step is for configuring the hardware's pins to be input or outputs, or anything else that must be set at pin level.

[mqtt_io.modules.gpio:GenericGPIO.setup_pin](https://github.com/flyte/mqtt-io/blob/develop/mqtt_io/modules/gpio/__init__.py#L117):

```python
def setup_pin(
    self,
    pin: PinType,
    direction: PinDirection,
    pullup: PinPUD,
    pin_config: ConfigType,
    initial: Optional[str] = None,
) -> None:
    """
    Called on initialisation of each pin of the GPIO module during the startup phase.

    The `pin_config` passed in here is the pin's entry in the `digital_inputs` or
    `digital_outputs` section of the config file.
    """
```

For example, it would be called three times given the following configuration:

```yaml
digital_inputs:
  - name: doorbell
    module: raspberrypi
    pin: 1

  - name: lightswitch
    module: raspberrypi
    pin: 2

digital_outputs:
  - name: lights
    module: raspberrypi
    pin: 3
```

Here's the `raspberrypi` GPIO module's `setup_pin()` implementation:

[mqtt_io.modules.gpio.raspberrypi:GPIO.setup_pin](https://github.com/flyte/mqtt-io/blob/develop/mqtt_io/modules/gpio/raspberrypi.py#L44):

```python
def setup_pin(
    self,
    pin: PinType,
    direction: PinDirection,
    pullup: PinPUD,
    pin_config: ConfigType,
    initial: Optional[str] = None,
) -> None:
    direction = self.direction_map[direction]
    pullup = self.pullup_map[pullup]

    initial_int = {None: -1, "low": 0, "high": 1}[initial]
    self.io.setup(pin, direction, pull_up_down=pullup, initial=initial_int)
```


## TODO

- Define when 'inverted' values are expected to be inverted or raw.