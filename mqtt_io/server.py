import asyncio
import logging
import re
from functools import partial, partialmethod
from hashlib import sha1
from importlib import import_module

from hbmqtt.client import ClientException, MQTTClient
from hbmqtt.mqtt.constants import QOS_1

from .config import (
    validate_and_normalise_config,
    validate_and_normalise_sensor_input_config,
)
from .events import EventBus
from .io import digital_input_poller, DigitalInputChangedEvent, SensorReadEvent
from .modules import BASE_SCHEMA as MODULE_BASE_SCHEMA
from .modules import install_missing_requirements
from .modules.gpio import PinDirection, PinPUD

_LOG = logging.getLogger(__name__)

SET_TOPIC = "set"
SET_ON_MS_TOPIC = "set_on_ms"
SET_OFF_MS_TOPIC = "set_off_ms"
OUTPUT_TOPIC = "output"
SENSOR_TOPIC = "sensor"

MODULE_IMPORT_PATH = "mqtt_io.modules"
MODULE_CLASS_NAMES = dict(gpio="GPIO", sensor="Sensor")


def _init_module(module_config, module_type):
    module = import_module(
        "%s.%s.%s" % (MODULE_IMPORT_PATH, module_type, module_config["module"])
    )
    # Doesn't need to be a deep copy because we're not mutating the base rules
    module_schema = MODULE_BASE_SCHEMA.copy()
    # Add the module's config schema to the base schema
    module_schema.update(getattr(module, "CONFIG_SCHEMA", {}))
    module_config = validate_and_normalise_config(module_config, module_schema)
    install_missing_requirements(module)
    return getattr(module, MODULE_CLASS_NAMES[module_type])(module_config)


async def set_output(module, output_config, payload):
    pin = output_config["pin"]
    if payload == output_config["on_payload"]:
        await module.async_set_pin(pin, True)
    elif payload == output_config["off_payload"]:
        await module.async_set_pin(pin, False)
    else:
        _LOG.warning("Payload received did not match 'on' or 'off' payloads: %r", payload)


class MqttGpio:
    def __init__(self, config):
        self.config = config
        self.gpio_configs = {}
        self.sensor_configs = {}
        self.digital_input_configs = {}
        self.digital_output_configs = {}
        self.sensor_input_configs = {}
        self.gpio_modules = {}
        self.sensor_modules = {}
        self.module_output_queues = {}

        self.loop = asyncio.get_event_loop()
        self.unawaited_tasks = []

        self.event_bus = EventBus(self.loop)

    # Init methods

    def _init_gpio_modules(self):
        self.gpio_configs = {x["name"]: x for x in self.config["gpio_modules"]}
        self.gpio_modules = {}
        for gpio_config in self.config["gpio_modules"]:
            self.gpio_modules[gpio_config["name"]] = _init_module(gpio_config, "gpio")

    def _init_sensor_modules(self):
        self.sensor_configs = {x["name"]: x for x in self.config["sensor_modules"]}
        self.sensor_modules = {}
        for sens_config in self.config["sensor_modules"]:
            self.sensor_modules[sens_config["name"]] = _init_module(sens_config, "sensor")

    def _init_digital_inputs(self):
        self.digital_input_configs = {x["name"]: x for x in self.config["digital_inputs"]}

        # Set up MQTT publish callback for input event
        async def publish_callback(event):
            in_conf = self.digital_input_configs[event.input_name]
            val = in_conf["on_payload"] if event.to_value else in_conf["off_payload"]
            await self.mqtt.publish(
                "%s/input/%s" % (self.config["mqtt"]["topic_prefix"], event.input_name),
                val.encode("utf8"),
            )

        self.event_bus.subscribe(DigitalInputChangedEvent, publish_callback)

        for in_conf in self.config["digital_inputs"]:
            pud = None
            if in_conf["pullup"]:
                pud = PinPUD.UP
            elif in_conf["pulldown"]:
                pud = PinPUD.DOWN
            module = self.gpio_modules[in_conf["module"]]
            module.setup_pin(in_conf["pin"], PinDirection.INPUT, pud, in_conf)

            # Start poller task
            self.unawaited_tasks.append(
                self.loop.create_task(
                    digital_input_poller(self.event_bus, module, in_conf)
                )
            )

    def _init_digital_outputs(self):
        self.digital_output_configs = {
            x["name"]: x for x in self.config["digital_outputs"]
        }
        # IDEA: Possible implementations -@flyte at 07/04/2019, 15:34:54
        # Could this be done asynchronously?
        for out_conf in self.config["digital_outputs"]:
            self.gpio_modules[out_conf["module"]].setup_pin(
                out_conf["pin"], PinDirection.OUTPUT, None, out_conf
            )
            # Create queues for each module with an output
            if out_conf["module"] not in self.module_output_queues:
                queue = asyncio.Queue()
                self.module_output_queues[out_conf["module"]] = queue

                # Create loops which handle new entries on the queue
                async def output_loop():
                    while True:
                        await set_output(*await queue.get())

                self.unawaited_tasks.append(self.loop.create_task(output_loop()))

    def _init_sensor_inputs(self):
        self.sensor_input_configs = {x["name"]: x for x in self.config["sensor_inputs"]}

        async def publish_sensor_callback(event):
            await self.mqtt.publish(
                "%s/%s/%s"
                % (self.config["mqtt"]["topic_prefix"], SENSOR_TOPIC, event.sensor_name),
                str(event.value).encode("utf8"),
            )

        self.event_bus.subscribe(SensorReadEvent, publish_sensor_callback)

        for sens_conf in self.config["sensor_inputs"]:
            sensor_module = self.sensor_modules[sens_conf["module"]]
            validate_and_normalise_sensor_input_config(sens_conf, sensor_module)
            sensor_module.setup_sensor()

            # Use default args to the function to get around the late binding closures
            async def poll_sensor(sensor_module=sensor_module, sens_conf=sens_conf):
                while True:
                    value = await sensor_module.async_get_value(sens_conf)
                    if value is not None:
                        value = round(value, sens_conf["digits"])
                        _LOG.info(
                            "Read sensor '%s' value of %s", sens_conf["name"], value
                        )
                        self.event_bus.fire(SensorReadEvent(sens_conf["name"], value))
                    await asyncio.sleep(sens_conf["interval"])

            self.unawaited_tasks.append(self.loop.create_task(poll_sensor()))

    async def _init_mqtt(self):
        config = self.config["mqtt"]
        topic_prefix = config["topic_prefix"]

        client_id = config["client_id"]
        if not client_id:
            client_id = "mqtt-gpio-%s" % sha1(topic_prefix.encode("utf8")).hexdigest()

        tls_enabled = config.get("tls", {}).get("enabled")

        uri = "mqtt%s://" % ("s" if tls_enabled else "")
        if config["user"] and config["password"]:
            uri += "%s:%s@" % (config["user"], config["password"])
        uri += "%s:%s" % (config["host"], config["port"])

        client_config = {}
        connect_kwargs = dict(cleansession=config["clean_session"])
        if tls_enabled:
            tls_config = config["tls"]
            if tls_config.get("certfile") and tls_config.get("keyfile"):
                client_config.update(
                    dict(
                        certfile=tls_config.get("certfile") or None,
                        keyfile=tls_config.get("keyfile") or None,
                    )
                )
            client_config["check_hostname"] = not tls_config["insecure"]
            connect_kwargs.update(
                dict(
                    capath=tls_config.get("ca_certs"),
                    cafile=tls_config.get("ca_file"),
                    cadata=tls_config.get("ca_data"),
                )
            )

        self.mqtt = MQTTClient(client_id=client_id, config=client_config, loop=self.loop)
        _LOG.info("Connected to MQTT")
        await self.mqtt.connect(uri, **connect_kwargs)
        for out_conf in self.digital_output_configs.values():
            for suffix in (SET_TOPIC, SET_ON_MS_TOPIC, SET_OFF_MS_TOPIC):
                topic = "%s/%s/%s/%s" % (
                    topic_prefix,
                    OUTPUT_TOPIC,
                    out_conf["name"],
                    suffix,
                )
                await self.mqtt.subscribe([(topic, QOS_1)])
                _LOG.info("Subscribed to topic: %r", topic)

    # Runtime methods

    def _handle_mqtt_msg(self, topic, payload):
        topic_prefix = self.config["mqtt"]["topic_prefix"]

        if not any(
            topic.endswith("/%s" % x)
            for x in (SET_TOPIC, SET_ON_MS_TOPIC, SET_OFF_MS_TOPIC)
        ):
            _LOG.debug(
                "Ignoring message to topic '%s' which doesn't end with '/set' etc.", topic
            )
            return
        try:
            output_name = output_name_from_topic(topic, topic_prefix)
        except ValueError as e:
            _LOG.warning("Unable to parse topic: %s", e)
            return
        output_config = self.digital_output_configs[output_name]
        module = self.gpio_modules[output_config["module"]]
        if topic.endswith("/%s" % SET_TOPIC):
            # This is a message to set a digital output to a given value
            self.module_output_queues[output_config["module"]].put_nowait(
                (module, output_config, payload)
            )
        else:
            value = topic.endswith("/%s" % SET_ON_MS_TOPIC)
            if output_config["inverted"]:
                value = not value

            async def set_ms():
                try:
                    secs = float(payload) / 1000
                except ValueError:
                    _LOG.warning(
                        "Unable to parse ms value as float from payload %r", payload
                    )
                    return
                await module.async_set_pin(output_config["pin"], value)
                await asyncio.sleep(secs)
                await module.async_set_pin(output_config["pin"], not value)

            task = self.loop.create_task(set_ms())
            self.unawaited_tasks.append(task)

    # Tasks

    async def _mqtt_rx_loop(self):
        try:
            while True:
                msg = await self.mqtt.deliver_message()
                topic = msg.publish_packet.variable_header.topic_name
                payload = msg.publish_packet.payload.data.decode("utf8")
                _LOG.info("Received message on topic %r: %r", topic, payload)
                self._handle_mqtt_msg(topic, payload)
        finally:
            _LOG.info("Disconnecting from MQTT...")
            await self.mqtt.disconnect()
            _LOG.info("MQTT disconnected")

    async def remove_finished_tasks(self):
        while True:
            await asyncio.sleep(1)
            finished_tasks = [x for x in self.unawaited_tasks if x.done()]
            if not finished_tasks:
                continue
            for task in finished_tasks:
                try:
                    await task
                except Exception as e:
                    _LOG.exception("Exception in task: %r:", task)
            self.unawaited_tasks = list(
                filter(lambda x: not x.done(), self.unawaited_tasks)
            )

    # Main entry point

    def run(self):
        self._init_gpio_modules()
        # Init the outputs before MQTT so we have some topics to subscribe to
        self._init_digital_outputs()

        # Get connected to the MQTT server
        self.loop.run_until_complete(self._init_mqtt())

        # Init the inputs after MQTT so we can start publishing right away
        self._init_sensor_modules()
        self._init_digital_inputs()
        self._init_sensor_inputs()

        # IDEA: Possible implementations -@flyte at 26/05/2019, 16:04:46
        # This is where we add any other async tasks that we want to run, such as polling
        # inputs, sensor loops etc.
        tasks = asyncio.gather(self._mqtt_rx_loop(), self.remove_finished_tasks())
        try:
            self.loop.run_until_complete(tasks)
        except KeyboardInterrupt:
            tasks.cancel()
            for task in list(self.mqtt.client_tasks) + self.unawaited_tasks:
                task.cancel()
            self.loop.run_until_complete(
                asyncio.gather(
                    *(self.unawaited_tasks + [tasks] + list(self.mqtt.client_tasks)),
                    return_exceptions=True,
                )
            )
        finally:
            for gpio_module in self.gpio_modules.values():
                try:
                    gpio_module.cleanup()
                except Exception:
                    _LOG.exception(
                        "Exception while cleaning up gpio module %s", gpio_module
                    )
            for sens_module in self.sensor_modules.values():
                try:
                    sens_module.cleanup()
                except Exception:
                    _LOG.exception(
                        "Exception while cleaning up sensor module %s", sens_module
                    )


def output_name_from_topic(topic, prefix):
    match = re.match("^{}/{}/(.+?)/.+$".format(prefix, OUTPUT_TOPIC), topic)
    if match is None:
        raise ValueError("Topic %r does not adhere to expected structure" % topic)
    return match.group(1)
