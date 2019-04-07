import asyncio
import re
import logging
from functools import partial
from importlib import import_module

from . import mqtt
from .config import validate_and_normalise_config
from .modules import BASE_SCHEMA as MODULE_BASE_SCHEMA
from .modules import install_missing_requirements
from .modules.gpio import PinDirection, PinPUD

_LOG = logging.getLogger(__name__)

SET_TOPIC = "set"
OUTPUT_TOPIC = "output"

MODULE_CLASS_NAMES = dict(gpio="GPIO", sensor="Sensor")


class ModuleCommand:
    def __init__(self, output, _):
        self.output = output
        self._ = _


async def mqtt_dispatcher(mqtt):
    while True:
        msg = await mqtt.deliver_message()
        topic = msg.publish_packet.variable_header.topic_name
        payload = msg.publish_packet.payload.data

        # Pseudocode
        prefix, module_name, output, _ = re.match(r"xxxx", topic)
        module_cmd = ModuleCommand(output, _)
        MODULES = {}
        MODULES[module_name].queue.put_nowait(module_cmd)


def _init_gpio_module(module_config, module_type):
    module = import_module(
        "mqtt_gpio.modules.%s.%s" % (module_type, module_config["module"])
    )
    # Doesn't need to be a deep copy because we're not mutating the base rules
    module_schema = MODULE_BASE_SCHEMA.copy()
    # Add the module's config schema to the base schema
    module_schema.update(getattr(module, "CONFIG_SCHEMA", {}))
    module_config = validate_and_normalise_config(module_config, module_schema)
    install_missing_requirements(module)
    return getattr(module, MODULE_CLASS_NAMES[module_type])(module_config)


class MqttGpio:
    def __init__(self, config):
        self.config = config
        self.gpio_configs = {}
        self.digital_input_configs = {}
        self.digital_output_configs = {}
        self.gpio_modules = {}
        self.module_output_queues = {}

        self.loop = asyncio.get_event_loop()
        self.tasks = []

        self._init_gpio_modules()
        self._init_digital_inputs()
        self._init_digital_outputs()

    def _init_gpio_modules(self):
        self.gpio_configs = {x["name"]: x for x in self.config["gpio_modules"]}
        self.gpio_modules = {}
        for gpio_config in self.config["gpio_modules"]:
            self.gpio_modules[gpio_config["name"]] = _init_gpio_module(
                gpio_config, "gpio"
            )

    def _init_digital_inputs(self):
        self.digital_input_configs = {x["name"]: x for x in self.config["digital_inputs"]}
        # IDEA: Possible implementations -@flyte at 07/04/2019, 15:34:39
        # Could this be done asynchronously?
        for in_conf in self.config["digital_inputs"]:
            pud = None
            if in_conf["pullup"]:
                pud = PinPUD.UP
            elif in_conf["pulldown"]:
                pud = PinPUD.DOWN
            self.gpio_modules[in_conf["module"]].setup_pin(
                in_conf["pin"], PinDirection.INPUT, pud, in_conf
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
                        module, module_config, output_config, payload = await queue.get()
                        pin = output_config["pin"]
                        if payload == output_config["on_payload"]:
                            await module.async_set_pin(pin, True)
                        elif payload == output_config["off_payload"]:
                            await module.async_set_pin(pin, False)
                        else:
                            print("Payload was weird: %r" % payload)

                self.tasks.append(self.loop.create_task(output_loop()))

    async def _init_mqtt(self):
        self.mqtt = await mqtt.connect(self.config["mqtt"]["host"])
        await self.mqtt.subscribe([("mqtt_gpio/#", mqtt.QOS_1)])

    async def _mqtt_loop(self):
        try:
            while True:
                msg = await self.mqtt.deliver_message()
                topic = msg.publish_packet.variable_header.topic_name
                payload = msg.publish_packet.payload.data.decode("utf8")
                print("%s - %s" % (topic, payload))
                _LOG.info("Received message on topic %r: %r", topic, payload)
                if topic.endswith("/%s" % SET_TOPIC):
                    topic_prefix = self.config["mqtt"]["topic_prefix"]
                    lindex = len("%s/%s/" % (topic_prefix, OUTPUT_TOPIC))
                    rindex = -len(SET_TOPIC) - 1
                    output_name = topic[lindex:rindex]
                    output_config = self.digital_output_configs[output_name]
                    module_config = self.gpio_configs[output_config["module"]]
                    module = self.gpio_modules[output_config["module"]]
                    queue = self.module_output_queues[module_config["name"]]
                    queue.put_nowait((module, module_config, output_config, payload))
        finally:
            print("\nDisconnecting from MQTT...")
            await self.mqtt.disconnect()
            print("MQTT disconnected")

    def run(self):
        self.loop.run_until_complete(self._init_mqtt())
        tasks = asyncio.gather(self._mqtt_loop())
        try:
            self.loop.run_until_complete(tasks)
        except KeyboardInterrupt:
            tasks.cancel()
            for task in list(self.mqtt.client_tasks) + self.tasks:
                task.cancel()
            self.loop.run_until_complete(
                asyncio.gather(
                    *(self.tasks + [tasks] + list(self.mqtt.client_tasks)),
                    return_exceptions=True
                )
            )

    # async def output_loop(self):
    #     while True:
    #         item = await self.module_output_queues["stdio"].get()
    #         print("Got item! %r" % (item,))
