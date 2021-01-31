import asyncio
import logging
import re
import signal as signals
import threading
from concurrent.futures import Future as ConcurrentFuture
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from hashlib import sha1
from importlib import import_module

from hbmqtt.client import MQTTClient
from hbmqtt.mqtt.constants import QOS_1

from .config import (
    validate_and_normalise_config,
    validate_and_normalise_sensor_input_config,
)
from .constants import (
    INPUT_TOPIC,
    MODULE_CLASS_NAMES,
    MODULE_IMPORT_PATH,
    OUTPUT_TOPIC,
    SENSOR_TOPIC,
    SET_OFF_MS_TOPIC,
    SET_ON_MS_TOPIC,
    SET_TOPIC,
)
from .events import EventBus
from .home_assistant import (
    hass_announce_digital_input,
    hass_announce_digital_output,
    hass_announce_sensor_input,
)
from .io import (
    DigitalInputChangedEvent,
    DigitalOutputChangedEvent,
    SensorReadEvent,
)
from .modules import BASE_SCHEMA as MODULE_BASE_SCHEMA
from .modules import install_missing_requirements
from .modules.gpio import InterruptEdge, InterruptSupport, PinDirection, PinPUD

_LOG = logging.getLogger(__name__)


def _init_module(module_config, module_type):
    """
    Initialise a GPIO module by:
    - Importing it
    - Validating its config
    - Installing any missing requirements for it
    - Instantiating its class
    """
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


def output_name_from_topic(topic, prefix):
    match = re.match("^{}/{}/(.+?)/.+$".format(prefix, OUTPUT_TOPIC), topic)
    if match is None:
        raise ValueError("Topic %r does not adhere to expected structure" % topic)
    return match.group(1)


class MqttIo:
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
        self.tasks = []
        self.unawaited_tasks = []

        self.event_bus = EventBus(self.loop)
        self.mqtt = None
        self.interrupt_locks = {}

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
                "%s/%s/%s"
                % (self.config["mqtt"]["topic_prefix"], INPUT_TOPIC, event.input_name),
                val.encode("utf8"),
            )

        self.event_bus.subscribe(DigitalInputChangedEvent, publish_callback)

        for in_conf in self.config["digital_inputs"]:
            module = self.gpio_modules[in_conf["module"]]
            module.setup_pin(PinDirection.INPUT, in_conf)

            interrupt = in_conf.get("interrupt")
            interrupt_for = in_conf.get("interrupt_for")

            # Only start the poller task if this _isn't_ set up with an interrupt, or if
            # it _is_ an interrupt, but it's used for triggering remote interrupts.
            # TODO: Tasks pending completion -@flyte at 31/01/2021, 11:01:56
            # Make this configurable?
            if interrupt is None or interrupt_for:
                self.unawaited_tasks.append(
                    self.loop.create_task(self.digital_input_poller(module, in_conf))
                )

            if interrupt is None:
                return

            edge = {
                "rising": InterruptEdge.RISING,
                "falling": InterruptEdge.FALLING,
                "both": InterruptEdge.BOTH,
            }[interrupt]
            if module.INTERRUPT_SUPPORT & InterruptSupport.SOFTWARE_CALLBACK:
                self.interrupt_locks[in_conf["name"]] = threading.Lock()
                # If it's a software callback interrupt, then supply
                # partial(self.interrupt_callback, module, in_conf["pin"])
                # as the callback.
                callback = partial(self.interrupt_callback, module, in_conf["pin"])
                module.setup_interrupt(in_conf["pin"], edge, callback, in_conf)
            else:
                # Else, just call module.setup_interrupt() without a callback
                module.setup_interrupt(in_conf["pin"], edge, in_conf)

    def _init_digital_outputs(self):
        self.digital_output_configs = {
            x["name"]: x for x in self.config["digital_outputs"]
        }

        # Set up MQTT publish callback for output event
        async def publish_callback(event):
            out_conf = self.digital_output_configs[event.output_name]
            val = out_conf["on_payload"] if event.to_value else out_conf["off_payload"]
            await self.mqtt.publish(
                "%s/output/%s" % (self.config["mqtt"]["topic_prefix"], event.output_name),
                val.encode("utf8"),
                qos=1,
                retain=out_conf["retain"],
            )

        self.event_bus.subscribe(DigitalOutputChangedEvent, publish_callback)

        for out_conf in self.config["digital_outputs"]:
            self.gpio_modules[out_conf["module"]].setup_pin(PinDirection.OUTPUT, out_conf)

            # Create queues for each module with an output
            if out_conf["module"] not in self.module_output_queues:
                queue = asyncio.Queue()
                self.module_output_queues[out_conf["module"]] = queue

                # Use partial to avoid late binding closure
                self.unawaited_tasks.append(
                    self.loop.create_task(partial(self.digital_output_loop, queue)())
                )

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
            sensor_module.setup_sensor(sens_conf)

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
            client_id = "mqtt-io-%s" % sha1(topic_prefix.encode("utf8")).hexdigest()

        tls_enabled = config.get("tls", {}).get("enabled")

        uri = "mqtt%s://" % ("s" if tls_enabled else "")
        if config["user"] and config["password"]:
            uri += "%s:%s@" % (config["user"], config["password"])
        uri += "%s:%s" % (config["host"], config["port"])

        client_config = dict(
            keep_alive=config["keepalive"],
        )
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
        client_config["will"] = dict(
            retain=True,
            topic="%s/%s" % (topic_prefix, config["status_topic"]),
            message=config["status_payload_dead"].encode("utf8"),
            qos=1,
        )

        self.mqtt = MQTTClient(client_id=client_id, config=client_config, loop=self.loop)
        _LOG.info("Connecting to MQTT...")
        await self.mqtt.connect(uri, **connect_kwargs)
        _LOG.info("Connected to MQTT")
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

        await self.mqtt.publish(
            "%s/%s" % (topic_prefix, config["status_topic"]),
            config["status_payload_running"].encode("utf8"),
            qos=1,
            retain=True,
        )
        # Publish initial values of outputs if desired
        for out_conf in self.digital_output_configs.values():
            if not out_conf["publish_initial"]:
                continue
            value = out_conf["initial"] == "high"
            payload = (
                out_conf["on_payload"]
                if value != out_conf["inverted"]
                else out_conf["off_payload"]
            )
            await self.mqtt.publish(
                "%s/output/%s" % (topic_prefix, out_conf["name"]),
                payload.encode("utf8"),
                qos=1,
                retain=out_conf["retain"],
            )
        # Publish Home Assistant Discovery messages if desired
        if config["discovery"]:
            for in_conf in self.digital_input_configs.values():
                await hass_announce_digital_input(in_conf, config, self.mqtt)
            for out_conf in self.digital_output_configs.values():
                await hass_announce_digital_output(out_conf, config, self.mqtt)
            for sens_conf in self.sensor_configs.values():
                await hass_announce_sensor_input(sens_conf, config, self.mqtt)

    # Runtime methods

    async def digital_input_poller(self, module, in_conf):
        last_value = None
        while True:
            value = await module.async_get_pin(in_conf["pin"])
            if value != last_value:
                _LOG.info(
                    "Digital input '%s' value changed to %s", in_conf["name"], value
                )
                self.event_bus.fire(
                    DigitalInputChangedEvent(in_conf["name"], last_value, value)
                )
                last_value = value
            # If the value is now the same as the 'interrupt' value (falling, rising)
            # and we're a remote interrupt then just trigger the remote interrupt
            interrupt = in_conf.get("interrupt")
            interrupt_for = in_conf.get("interrupt_for")
            if not interrupt or not interrupt_for:
                continue
            if not any(
                (
                    interrupt == "rising" and value,
                    interrupt == "falling" and not value,
                    # Doesn't work for 'both' because there's no one 'triggered' state
                    # to check if we're stuck in.
                    # interrupt == "both",
                )
            ):
                continue
            interrupt_lock = self.interrupt_locks[in_conf["name"]]
            if not interrupt_lock.acquire(blocking=False):
                _LOG.debug(
                    (
                        "Polled an interrupt value on pin '%s', but we're "
                        "not triggering the remote interrupt because we're "
                        "already handling it."
                    ),
                    in_conf["name"],
                )
                continue
            _LOG.debug(
                "Polled value of %s on '%s' triggered remote interrupt",
                value,
                in_conf["name"],
            )
            self.handle_remote_interrupt(interrupt_for, interrupt_lock)
            # TODO: Tasks pending completion -@flyte at 29/05/2019, 01:02:50
            # Make this delay configurable in in_conf
            await asyncio.sleep(0.1)

    def interrupt_callback(self, module, pin, *args, **kwargs):
        pin_name = module.pin_configs[pin]["name"]
        interrupt_lock = self.interrupt_locks[pin_name]
        if not interrupt_lock.acquire(blocking=False):
            _LOG.debug(
                (
                    "Ignoring interrupt on pin '%s' because we're already busy "
                    "processing one."
                ),
                pin_name,
            )
            return
        try:
            _LOG.info("Handling interrupt callback on pin '%s'", pin_name)
            remote_interrupt_for_pin_names = module.remote_interrupt_for(pin)

            if remote_interrupt_for_pin_names:
                _LOG.debug("Interrupt on '%s' triggered remote interrupt.", pin_name)
                return self.handle_remote_interrupt(
                    remote_interrupt_for_pin_names, interrupt_lock
                )
            _LOG.debug("Interrupt is for the '%s' pin itself", pin_name)
            value = module.get_interrupt_value(pin, *args, **kwargs)
            self.event_bus.fire(DigitalInputChangedEvent(pin_name, None, value))
        finally:
            if not remote_interrupt_for_pin_names:
                interrupt_lock.release()

    def handle_remote_interrupt(self, pin_names, interrupt_lock):
        # TODO: Tasks pending completion -@flyte at 30/01/2021, 13:14:44
        # Lock this interrupt
        # IDEA: Possible implementations -@flyte at 30/01/2021, 16:09:35
        # Does the interrupt_for module say that its interrupt pin will be held low
        # until the interrupt register is read, or does it just pulse its interrupt
        # pin?
        _LOG.debug("Interrupt is for pins: '%s'", "', '".join(pin_names))
        remote_modules_and_pins = {}
        for remote_pin_name in pin_names:
            in_conf = self.digital_input_configs[remote_pin_name]
            remote_module = self.gpio_modules[in_conf["module"]]
            remote_modules_and_pins.setdefault(remote_module, []).append(in_conf["pin"])

        remote_interrupt_tasks = []
        for remote_module, pins in remote_modules_and_pins.items():

            async def handle_remote_interrupt_task(
                remote_module=remote_module, pins=pins
            ):
                interrupt_values = await remote_module.get_interrupt_values_remote(pins)
                for pin, value in interrupt_values.items():
                    remote_pin_name = remote_module.pin_configs[pin]["name"]
                    self.event_bus.fire(
                        DigitalInputChangedEvent(remote_pin_name, None, value)
                    )

            remote_interrupt_tasks.append(handle_remote_interrupt_task)

        async def await_remote_interrupts():
            try:
                await asyncio.gather(*remote_interrupt_tasks)
            finally:
                interrupt_lock.release()

        task = asyncio.run_coroutine_threadsafe(await_remote_interrupts(), self.loop)
        self.unawaited_tasks.append(task)
        # TODO: Tasks pending completion -@flyte at 30/01/2021, 13:15:12
        # Unlock this interrupt

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
            # This must be a set_on_ms or set_off_ms topic
            desired_value = topic.endswith("/%s" % SET_ON_MS_TOPIC)

            async def set_ms():
                """
                Create this task to directly set the outputs, as we don't want to tie up
                the set_digital_output loop. Creating a bespoke task for the job is the
                simplest and most effective way of leveraging the asyncio framework.
                """
                try:
                    secs = float(payload) / 1000
                except ValueError:
                    _LOG.warning(
                        "Unable to parse ms value as float from payload %r", payload
                    )
                    return
                _LOG.info(
                    "Turning output '%s' %s for %s second(s)",
                    output_config["name"],
                    "on" if desired_value else "off",
                    secs,
                )
                await self.set_digital_output(module, output_config, desired_value)
                await asyncio.sleep(secs)
                _LOG.info(
                    "Turning output '%s' %s after %s second(s) elapsed",
                    output_config["name"],
                    "off" if desired_value else "on",
                    secs,
                )
                await self.set_digital_output(module, output_config, not desired_value)

            task = self.loop.create_task(set_ms())
            self.unawaited_tasks.append(task)

    async def set_digital_output(self, module, output_config, value):
        """
        Set a digital output, taking into account whether it's configured
        to be inverted.
        """
        set_value = value != output_config["inverted"]
        await module.async_set_pin(output_config["pin"], set_value)
        _LOG.info(
            "Digital output '%s' set to %s (%s)",
            output_config["name"],
            set_value,
            "on" if value else "off",
        )
        self.event_bus.fire(DigitalOutputChangedEvent(output_config["name"], value))

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
            await self.mqtt.publish(
                "%s/%s"
                % (
                    self.config["mqtt"]["topic_prefix"],
                    self.config["mqtt"]["status_topic"],
                ),
                self.config["mqtt"]["status_payload_stopped"].encode("utf8"),
                qos=1,
                retain=True,
            )
            _LOG.info("Disconnecting from MQTT...")
            await self.mqtt.disconnect()
            _LOG.info("MQTT disconnected")

    async def _remove_finished_tasks(self):
        while True:
            await asyncio.sleep(1)
            finished_tasks = [x for x in self.unawaited_tasks if x.done()]
            if not finished_tasks:
                continue
            for task in finished_tasks:
                if isinstance(task, ConcurrentFuture):
                    # task = self.loop.run_in_executor(ThreadPoolExecutor(), task)
                    task = asyncio.wrap_future(task)
                try:
                    await task
                except Exception:  # pylint: disable=broad-except
                    _LOG.exception("Exception in task: %r:", task)
            self.unawaited_tasks = list(
                filter(lambda x: not x.done(), self.unawaited_tasks)
            )

    async def digital_output_loop(self, queue):
        """
        Handle digital output MQTT messages for a specific GPIO module.
        An instance of this loop will be created for each individual GPIO module so that
        when messages come in via MQTT, we don't have to wait for some other module's
        action to complete before carrying out this one.

        It may seem like we should use this loop to handle /set_on_ms and /set_off_ms
        messages, but it's actually better that we don't, since any timed stuff would
        hold up /set messages that need to take place immediately.
        """
        while True:
            module, output_config, payload = await queue.get()
            if payload not in (output_config["on_payload"], output_config["off_payload"]):
                _LOG.warning(
                    "'%s' is not a valid payload for output %s. Only '%s' and '%s' are allowed.",
                    payload,
                    output_config["name"],
                    output_config["on_payload"],
                    output_config["off_payload"],
                )
                continue

            value = payload == output_config["on_payload"]
            await self.set_digital_output(module, output_config, value)

            try:
                ms = output_config["timed_set_ms"]
            except KeyError:
                continue

            async def reset_timer():
                """
                Reset the output to the opposite value after x ms.
                """
                await asyncio.sleep(ms / 1000.0)
                _LOG.info(
                    (
                        "Setting digital output '%s' back to its previous value after "
                        "configured 'timed_set_ms' delay of %sms"
                    ),
                    output_config["name"],
                    ms,
                )
                await self.set_digital_output(module, output_config, not value)

            task = self.loop.create_task(reset_timer())
            self.unawaited_tasks.append(task)

    # Main entry point

    def run(self):
        for s in (signals.SIGHUP, signals.SIGTERM, signals.SIGINT):
            self.loop.add_signal_handler(
                s, lambda s=s: self.loop.create_task(self.shutdown(s))
            )
        self._init_gpio_modules()
        # Init the outputs before MQTT so we have some topics to subscribe to
        self._init_digital_outputs()

        # Get connected to the MQTT server
        self.loop.run_until_complete(self._init_mqtt())

        # Init the inputs after MQTT so we can start publishing right away
        self._init_sensor_modules()
        self._init_digital_inputs()
        self._init_sensor_inputs()

        # This is where we add any other async tasks that we want to run, such as polling
        # inputs, sensor loops etc.
        self.tasks = [
            self.loop.create_task(coro)
            for coro in (self._mqtt_rx_loop(), self._remove_finished_tasks())
        ]
        try:
            self.loop.run_forever()
        finally:
            self.loop.close()
            _LOG.debug("Loop closed")
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
        _LOG.debug("run() complete")

    async def shutdown(self, signal):
        _LOG.warning("Received exit signal %s", signal.name)

        # Cancel our main task first so we don't mess the MQTT library's connection
        for t in self.tasks:
            t.cancel()
        _LOG.info("Waiting for main task to complete...")
        all_done = False
        while not all_done:
            all_done = all(t.done() for t in self.tasks)
            await asyncio.sleep(0.1)

        current_task = asyncio.Task.current_task()
        tasks = [
            t
            for t in asyncio.Task.all_tasks(loop=self.loop)
            if not t.done() and t is not current_task
        ]
        _LOG.info("Cancelling %s remaining tasks", len(tasks))
        for t in tasks:
            t.cancel()
        _LOG.info("Waiting for %s remaining tasks to complete...", len(tasks))
        all_done = False
        while not all_done:
            all_done = all(t.done() for t in tasks)
            await asyncio.sleep(0.1)
        _LOG.debug("Tasks all finished. Stopping loop...")
        self.loop.stop()
        _LOG.debug("Loop stopped")
