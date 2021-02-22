import argparse
import json
import logging
import logging.config
import socket
import ssl
import sys
import threading
from functools import reduce
from hashlib import sha1
from importlib import import_module
from time import sleep, time

import cerberus
import paho.mqtt.client as mqtt
import yaml

from pi_mqtt_gpio import CONFIG_SCHEMA
from pi_mqtt_gpio.modules import BASE_SCHEMA, InterruptEdge, PinDirection, PinPullup
from pi_mqtt_gpio.scheduler import Scheduler, Task

try:
    from math import gcd
except ImportError:
    from fractions import gcd

LOG_LEVEL_MAP = {
    mqtt.MQTT_LOG_INFO: logging.INFO,
    mqtt.MQTT_LOG_NOTICE: logging.INFO,
    mqtt.MQTT_LOG_WARNING: logging.WARNING,
    mqtt.MQTT_LOG_ERR: logging.ERROR,
    mqtt.MQTT_LOG_DEBUG: logging.DEBUG,
}

RECONNECT_DELAY_SECS = 5
GPIO_MODULES = {}  # storage for gpio modules
SENSOR_MODULES = {}  # storage for sensor modules
STREAM_MODULES = {}  # storage for stream modules
GPIO_CONFIGS = {}  # storage for gpios
SENSOR_CONFIGS = {}  # storage for sensors
STREAM_CONFIGS = {}  # storage for streams
SENSOR_INPUT_CONFIGS = {}  # storage for sensor input configs
STREAM_READ_CONFIGS = {}  # storage for streams read configs
STREAM_WRITE_CONFIGS = {}  # storage for streams write configs
LAST_STATES = {}
GPIO_INTERRUPT_LOOKUP = {}
SET_TOPIC = "set"
SET_ON_MS_TOPIC = "set_on_ms"
SET_OFF_MS_TOPIC = "set_off_ms"
OUTPUT_TOPIC = "output"
INPUT_TOPIC = "input"
SENSOR_TOPIC = "sensor"
STREAM_TOPIC = "stream"

_LOG = logging.getLogger("mqtt_gpio")


class CannotInstallModuleRequirements(Exception):
    pass


class InvalidPayload(Exception):
    pass


class ModuleConfigInvalid(Exception):
    def __init__(self, errors, *args, **kwargs):
        self.errors = errors
        super(ModuleConfigInvalid, self).__init__(*args, **kwargs)


class ConfigValidator(cerberus.Validator):
    """
    Cerberus Validator containing function(s) for use with validating or
    coercing values relevant to the pi_mqtt_gpio project.
    """

    @staticmethod
    def _normalize_coerce_rstrip_slash(value):
        """
        Strip forward slashes from the end of the string.
        :param value: String to strip forward slashes from
        :type value: str
        :return: String without forward slashes on the end
        :rtype: str
        """
        return value.rstrip("/")

    @staticmethod
    def _normalize_coerce_tostring(value):
        """
        Convert value to string.
        :param value: Value to convert
        :return: Value represented as a string.
        :rtype: str
        """
        return str(value)


def on_log(client, userdata, level, buf):
    """
    Called when MQTT client wishes to log something.
    :param client: MQTT client instance
    :param userdata: Any user data set in the client
    :param level: MQTT log level
    :param buf: The log message buffer
    :return: None
    :rtype: NoneType
    """
    _LOG.log(LOG_LEVEL_MAP[level], "MQTT client: %s" % buf)


def output_by_name(output_name):
    """
    Returns the output configuration for a given output name.
    :param output_name: The name of the output
    :type output_name: str
    :return: The output configuration or None if not found
    :rtype: dict
    """
    for output in digital_outputs:
        if output["name"] == output_name:
            return output
    _LOG.warning("No output found with name of %r", output_name)


def stream_write_by_name(name):
    """
    Returns the stream write configuration for a given name.
    :param name: The name of the write
    :type output_name: str
    :return: The output configuration or None if not found
    :rtype: dict
    """
    for write in stream_writes:
        if write["name"] == name:
            return write
    _LOG.warning("No write found with name of %r", name)


def set_pin(topic_prefix, output_config, value):
    """
    Sets the output pin to a new value and publishes it on MQTT.
    :param topic_prefix: the name of the topic, the pin is published
    :type topic_prefix: string
    :param output_config: The output configuration
    :type output_config: dict
    :param value: The new value to set it to
    :type value: bool
    :return: None
    :rtype: NoneType
    """
    gpio = GPIO_MODULES[output_config["module"]]
    set_value = not value if output_config["inverted"] else value
    gpio.set_pin(output_config["pin"], set_value)
    _LOG.info(
        "Set %r output %r to %r",
        output_config["module"],
        output_config["name"],
        set_value,
    )
    payload = output_config["on_payload" if value else "off_payload"]
    client.publish(
        "%s/%s/%s" % (topic_prefix, OUTPUT_TOPIC, output_config["name"]),
        retain=output_config["retain"],
        payload=payload,
    )


def stream_write_output(topic_prefix, stream_write_config, data):
    """
    Writes data to stream
    :param topic_prefix: the name of the topic, the pin is published
    :type topic_prefix: string
    :param stream_write_config: The write stream configuration
    :type stream_write_config: dict
    :param data: data to write
    :type value: string
    :return: None
    :rtype: NoneType
    """
    sw = STREAM_MODULES[stream_write_config["module"]]
    sw.write(stream_write_config["name"], data.encode("utf-8"))
    _LOG.info(
        "Write %r %r write %s",
        stream_write_config["module"],
        stream_write_config["name"],
        data,
    )


def get_pin(in_conf, module):
    """
    Gets a pin using a GPIO module. Inverts the state if set in config."
    :param in_conf: The input config
    :type in_conf: dict
    :param module: The GPIO module
    :type module: modules.GenericGPIO
    :return: The value of the pin, inverted if desired
    :rtype: bool
    """
    state = bool(module.get_pin(in_conf["pin"]))
    return state != in_conf["inverted"]


def handle_set(topic_prefix, msg):
    """
    Handles an incoming 'set' MQTT message.
    :param topic_prefix: the name of the topic, the pin is published
    :type topic_prefix: string
    :param msg: The incoming MQTT message
    :type msg: paho.mqtt.client.MQTTMessage
    :return: None
    :rtype: NoneType
    """
    output_name = output_name_from_topic(msg.topic, topic_prefix, SET_TOPIC)
    output_config = output_by_name(output_name)
    if output_config is None:
        return
    payload = msg.payload.decode("utf8")
    if payload not in (output_config["on_payload"], output_config["off_payload"]):
        _LOG.warning(
            "Payload %r does not relate to configured on/off values %r and %r",
            payload,
            output_config["on_payload"],
            output_config["off_payload"],
        )
        return

    value = payload == output_config["on_payload"]
    set_pin(topic_prefix, output_config, value)

    try:
        ms = output_config["timed_set_ms"]
    except KeyError:
        return
    scheduler.add_task(
        Task(time() + ms / 1000.0, set_pin, topic_prefix, output_config, not value)
    )
    _LOG.info(
        "Scheduled output %r to change back to %r after %r ms.",
        output_config["name"],
        not value,
        ms,
    )


def handle_set_ms(topic_prefix, msg, value):
    """
    Handles an incoming 'set_<on/off>_ms' MQTT message.
    :param topic_prefix: the name of the topic
    :type topic_prefix: string
    :param msg: The incoming MQTT message
    :type msg: paho.mqtt.client.MQTTMessage
    :param value: The value to set the output to
    :type value: bool
    :return: None
    :rtype: NoneType
    """
    try:
        ms = int(msg.payload)
    except ValueError:
        raise InvalidPayload("Could not parse ms value %r to an integer." % msg.payload)
    suffix = SET_ON_MS_TOPIC if value else SET_OFF_MS_TOPIC
    output_name = output_name_from_topic(msg.topic, topic_prefix, suffix)
    output_config = output_by_name(output_name)
    if output_config is None:
        return

    set_pin(topic_prefix, output_config, value)
    scheduler.add_task(
        Task(time() + ms / 1000.0, set_pin, topic_prefix, output_config, not value)
    )
    _LOG.info(
        "Scheduled output %r to change back to %r after %r ms.",
        output_config["name"],
        not value,
        ms,
    )


def handle_raw(topic_prefix, msg):
    """
    Handles an incoming raw MQTT message.
    :param topic_prefix: the name of the topic
    :type topic_prefix: string
    :param msg: The incoming MQTT message
    :type msg: paho.mqtt.client.MQTTMessage
    :return: None
    :rtype: NoneType
    """
    stream_write_name = stream_write_name_from_topic(msg.topic, topic_prefix)
    stream_write_config = stream_write_by_name(stream_write_name)
    if stream_write_config is None:
        return
    payload = msg.payload.decode("string_escape")
    stream_write_output(topic_prefix, stream_write_config, payload)


def install_missing_requirements(module):
    """
    Some of the modules require external packages to be installed. This gets
    the list from the `REQUIREMENTS` module attribute and attempts to
    install the requirements using pip.
    :param module: GPIO module
    :type module: ModuleType
    :return: None
    :rtype: NoneType
    """
    reqs = getattr(module, "REQUIREMENTS", [])
    if not reqs:
        _LOG.info("Module %r has no extra requirements to install.", module)
        return
    import pkg_resources

    pkgs_installed = pkg_resources.WorkingSet()
    pkgs_required = []
    for req in reqs:
        if pkgs_installed.find(pkg_resources.Requirement.parse(req)) is None:
            pkgs_required.append(req)
    if pkgs_required:
        from subprocess import CalledProcessError, check_call

        try:
            check_call([sys.executable, "-m", "pip", "install"] + pkgs_required)
        except CalledProcessError as err:
            raise CannotInstallModuleRequirements(
                "Unable to install packages for module %r (%s): %s"
                % (module, pkgs_required, err)
            )


def type_from_topic(topic, topic_prefix):
    """
    Return the topic type for this topic
    The topics are formatted as topic_prefix/type[/parameter...].
    The parameter section is optional.
    :param topic: String such as 'mytopicprefix/output/tv_lamp/set'
    :type topic: str
    :param topic_prefix: Prefix of our topicsclient,
    :type topic_prefix: str
    :return: Type for this topic
    :rtype: str
    """
    # Strip off the prefix
    lindex = len("%s/" % topic_prefix)
    s = topic[lindex:]
    # Get remaining fields, the first one is the type
    fields = s.split("/")
    return fields[0]


def output_name_from_topic(topic, topic_prefix, suffix):
    """
    Return the name of the output which the topic is setting.
    :param topic: String such as 'mytopicprefix/output/tv_lamp/set'
    :type topic: str
    :param topic_prefix: Prefix of our topicsclient,
    :type topic_prefix: str
    :param suffix: The suffix of the topic such as "set" or "set_ms"
    :type suffix: str
    :return: Name of the output this topic is setting
    :rtype: str
    """
    if not topic.endswith("/%s" % suffix):
        raise ValueError("This topic does not end with '/%s'" % suffix)
    lindex = len("%s/%s/" % (topic_prefix, OUTPUT_TOPIC))
    rindex = -len(suffix) - 1
    return topic[lindex:rindex]


def stream_write_name_from_topic(topic, topic_prefix):
    """
    Return the name of the stream write which the topic is setting.
    :param topic: String such as 'mytopicprefix/stream/tx'
    :type topic: str
    :param topic_prefix: Prefix of our topicsclient,
    :type topic_prefix: str
    :return: Name of the output this topic is setting
    :rtype: str
    """
    lindex = len("%s/%s/" % (topic_prefix, STREAM_TOPIC))
    return topic[lindex:]


def init_mqtt(config, digital_outputs, stream_writes):
    """
    Configure MQTT client.
    :param config: Validated config dict containing MQTT connection details
    :type config: dict
    :param digital_outputs: List of validated config dicts for digital outputs
    :type digital_outputs: list
    :param stream_writes: List of validated config dicts for stream writes
    :type stream_writes: list
    :return: Connected and initialised MQTT client
    :rtype: paho.mqtt.client.Client
    """
    global topic_prefix
    topic_prefix = config["topic_prefix"]
    protocol = mqtt.MQTTv311
    if config["protocol"] == "3.1":
        protocol = mqtt.MQTTv31

    # https://stackoverflow.com/questions/45774538/what-is-the-maximum-length-of-client-id-in-mqtt
    # TLDR: Soft limit of 23, but we needn't truncate it on our end.
    client_id = config["client_id"]
    if not client_id:
        client_id = "pi-mqtt-gpio-%s" % sha1(topic_prefix.encode("utf8")).hexdigest()

    client = mqtt.Client(client_id=client_id, clean_session=False, protocol=protocol)

    if config["user"] and config["password"]:
        client.username_pw_set(config["user"], config["password"])

    # Set last will and testament (LWT)
    status_topic = "%s/%s" % (topic_prefix, config["status_topic"])
    client.will_set(
        status_topic, payload=config["status_payload_dead"], qos=1, retain=True
    )
    _LOG.debug("Last will set on %r as %r.", status_topic, config["status_payload_dead"])

    # Set TLS options
    tls_enabled = config.get("tls", {}).get("enabled")
    if tls_enabled:
        tls_config = config["tls"]
        tls_kwargs = dict(
            ca_certs=tls_config.get("ca_certs"),
            certfile=tls_config.get("certfile"),
            keyfile=tls_config.get("keyfile"),
            ciphers=tls_config.get("ciphers"),
        )
        try:
            tls_kwargs["cert_reqs"] = getattr(ssl, tls_config["cert_reqs"])
        except KeyError:
            pass
        try:
            tls_kwargs["tls_version"] = getattr(ssl, tls_config["tls_version"])
        except KeyError:
            pass

        client.tls_set(**tls_kwargs)
        client.tls_insecure_set(tls_config["insecure"])

    def on_conn(client, userdata, flags, rc):
        """
        On connection to MQTT, subscribe to the relevant topics.
        :param client: Connected MQTT client instance
        :type client: paho.mqtt.client.Client
        :param userdata: User data
        :param flags: Response flags from the broker
        :type flags: dict
        :param rc: Response code from the broker
        :type rc: int
        :return: None
        :rtype: NoneType
        """
        if rc == 0:
            _LOG.info(
                "Connected to the MQTT broker with protocol v%s.", config["protocol"]
            )
            for out_conf in digital_outputs:
                for suffix in (SET_TOPIC, SET_ON_MS_TOPIC, SET_OFF_MS_TOPIC):
                    topic = "%s/%s/%s/%s" % (
                        topic_prefix,
                        OUTPUT_TOPIC,
                        out_conf["name"],
                        suffix,
                    )
                    client.subscribe(topic, qos=1)
                    _LOG.info("Subscribed to topic: %r", topic)
            for stream_write_conf in stream_writes:
                topic = "%s/%s/%s" % (
                    topic_prefix,
                    STREAM_TOPIC,
                    stream_write_conf["name"],
                )
                client.subscribe(topic, qos=1)
                _LOG.info("Subscribed to topic: %r", topic)
            client.publish(
                status_topic, config["status_payload_running"], qos=1, retain=True
            )
            # HASS
            if config["discovery"]:
                for in_conf in digital_inputs:
                    hass_announce_digital_input(in_conf, topic_prefix, config)
                for out_conf in digital_outputs:
                    hass_announce_digital_output(out_conf, topic_prefix, config)
                for in_conf in sensor_inputs:
                    hass_announce_sensor_input(in_conf, topic_prefix, config)
        elif rc == 1:
            _LOG.fatal("Incorrect protocol version used to connect to MQTT broker.")
            sys.exit(1)
        elif rc == 2:
            _LOG.fatal("Invalid client identifier used to connect to MQTT broker.")
            sys.exit(1)
        elif rc == 3:
            _LOG.warning("MQTT broker unavailable. Retrying in %s secs...")
            sleep(RECONNECT_DELAY_SECS)
            client.reconnect()
        elif rc == 4:
            _LOG.fatal("Bad username or password used to connect to MQTT broker.")
            sys.exit(1)
        elif rc == 5:
            _LOG.fatal("Not authorised to connect to MQTT broker.")
            sys.exit(1)

    def on_msg(client, userdata, msg):
        """
        On reception of MQTT message, set the relevant output to a new value.
        :param client: Connected MQTT client instance
        :type client: paho.mqtt.client.Client
        :param userdata: User data (any data type)
        :param msg: Received message instance
        :type msg: paho.mqtt.client.MQTTMessage
        :return: None
        :rtype: NoneType
        """
        try:
            topic_type = type_from_topic(msg.topic, topic_prefix)
            _LOG.info(
                "Received message on topic %r type: %r: %r",
                msg.topic,
                topic_type,
                msg.payload,
            )
            if topic_type == OUTPUT_TOPIC:
                if msg.topic.endswith("/%s" % SET_TOPIC):
                    handle_set(topic_prefix, msg)
                elif msg.topic.endswith("/%s" % SET_ON_MS_TOPIC):
                    handle_set_ms(topic_prefix, msg, True)
                elif msg.topic.endswith("/%s" % SET_OFF_MS_TOPIC):
                    handle_set_ms(topic_prefix, msg, False)
                else:
                    _LOG.warning("Unhandled output topic %r.", msg.topic)
            elif topic_type == STREAM_TOPIC:
                handle_raw(topic_prefix, msg)
            else:
                _LOG.warning("Unhandled topic %r.", msg.topic)
        except InvalidPayload as exc:
            _LOG.warning("Invalid payload on received MQTT message: %s" % exc)
        except Exception:
            _LOG.exception("Exception while handling received MQTT message:")

    client.on_connect = on_conn
    client.on_message = on_msg
    client.on_log = on_log

    return client


def configure_gpio_module(gpio_config):
    """
    Imports gpio module, validates its config and returns an instance of it.
    :param gpio_config: Module configuration values
    :type gpio_config: dict
    :return: Configured instance of the gpio module
    :rtype: pi_mqtt_gpio.modules.GenericGPIO
    """
    gpio_module = import_module("pi_mqtt_gpio.modules.%s" % gpio_config["module"])
    # Doesn't need to be a deep copy because we won't modify the base
    # validation rules, just add more of them.
    module_config_schema = BASE_SCHEMA.copy()
    module_config_schema.update(getattr(gpio_module, "CONFIG_SCHEMA", {}))
    module_validator = cerberus.Validator(module_config_schema)
    if not module_validator.validate(gpio_config):
        raise ModuleConfigInvalid(module_validator.errors)
    gpio_config = module_validator.normalized(gpio_config)
    install_missing_requirements(gpio_module)
    return gpio_module.GPIO(gpio_config)


def configure_sensor_module(sensor_config):
    """
    Imports sensor module, validates its config and returns an instance of it.
    :param sensor_config: Module configuration values
    :type sensor_config: dict
    :return: Configured instance of the sensor module
    :rtype: pi_mqtt_gpio.modules.GenericSensor
    """
    sensor_module = import_module("pi_mqtt_gpio.modules.%s" % sensor_config["module"])
    # Doesn't need to be a deep copy because we won't modify the base
    # validation rules, just add more of them.
    module_config_schema = BASE_SCHEMA.copy()
    module_config_schema.update(getattr(sensor_module, "CONFIG_SCHEMA", {}))
    module_validator = cerberus.Validator(module_config_schema)
    if not module_validator.validate(sensor_config):
        raise ModuleConfigInvalid(module_validator.errors)
    sensor_config = module_validator.normalized(sensor_config)
    install_missing_requirements(sensor_module)
    return sensor_module.Sensor(sensor_config)


def configure_stream_module(stream_config):
    """
    Imports stream module, validates its config and returns an instance of it.
    :param stream_config: Module configuration values
    :type stream_config: dict
    :return: Configured instance of the stream module
    :rtype: pi_mqtt_gpio.modules.GenericStream
    """
    stream_module = import_module("pi_mqtt_gpio.modules.%s" % stream_config["module"])
    # Doesn't need to be a deep copy because we won't modify the base
    # validation rules, just add more of them.
    module_config_schema = BASE_SCHEMA.copy()
    module_config_schema.update(getattr(stream_module, "CONFIG_SCHEMA", {}))
    module_validator = cerberus.Validator(module_config_schema)
    if not module_validator.validate(stream_config):
        raise ModuleConfigInvalid(module_validator.errors)
    stream_config = module_validator.normalized(stream_config)
    install_missing_requirements(stream_module)
    return stream_module.Stream(stream_config)


def initialise_digital_input(in_conf, gpio):
    """
    Initialises digital input.
    :param in_conf: Input config
    :type in_conf: dict
    :param gpio: Instance of GenericGPIO to use to configure the pin
    :type gpio: pi_mqtt_gpio.modules.GenericGPIO
    :return: None
    :rtype: NoneType
    """
    pin = in_conf["pin"]
    pud = None
    if in_conf["pullup"]:
        pud = PinPullup.UP
    elif in_conf["pulldown"]:
        pud = PinPullup.DOWN

    gpio.setup_pin(pin, PinDirection.INPUT, pud, in_conf)

    # try to initialize interrupt, if available
    if in_conf["interrupt"] != "none":
        try:
            edge = {
                "rising": InterruptEdge.RISING,
                "falling": InterruptEdge.FALLING,
                "both": InterruptEdge.BOTH,
            }[in_conf["interrupt"]]
        except KeyError as exc:
            _LOG.error(
                "initialise_digital_input: config value(%s) for 'interrupt' \
                 invalid in  entry '%s'",
                in_conf["interrupt"],
                in_conf["name"],
            )

        try:
            bouncetime = in_conf["bouncetime"]
            module = in_conf["module"]
            gpio.setup_interrupt(module, pin, edge, gpio_interrupt_callback, bouncetime)

            # store for callback function handling
            if not GPIO_INTERRUPT_LOOKUP.get(module):
                GPIO_INTERRUPT_LOOKUP[module] = {}
            if not GPIO_INTERRUPT_LOOKUP[module].get(pin):
                GPIO_INTERRUPT_LOOKUP[module][pin] = in_conf
        except NotImplementedError as exc:
            _LOG.error(
                "initialise_digital_input: interrupt not implemented for \
                 input(%s) on module(%s): %s",
                in_conf["name"],
                in_conf["module"],
                exc,
            )


def initialise_digital_output(out_conf, gpio):
    """
    Initialises digital output.
    :param out_conf: Output config
    :type out_conf: dict
    :param gpio: Instance of GenericGPIO to use to configure the pin
    :type gpio: pi_mqtt_gpio.modules.GenericGPIO
    :return: None
    :rtype: NoneType
    """
    gpio.setup_pin(out_conf["pin"], PinDirection.OUTPUT, None, out_conf)


def validate_sensor_input_config(sens_conf):
    """
    Validates sensor input config.
    :param sens_conf: Sensor input config
    :type sens_conf: dict
    :return: None
    :rtype: NoneType
    """
    sensor_module = import_module(
        "pi_mqtt_gpio.modules.%s" % SENSOR_CONFIGS[sens_conf["module"]]["module"]
    )
    # Doesn't need to be a deep copy because we won't modify the base
    # validation rules, just add more of them.
    sensor_input_schema = CONFIG_SCHEMA["sensor_inputs"]["schema"]["schema"].copy()
    sensor_input_schema.update(getattr(sensor_module, "SENSOR_SCHEMA", {}))
    sensor_validator = cerberus.Validator(sensor_input_schema)
    if not sensor_validator.validate(sens_conf):
        raise ModuleConfigInvalid(sensor_validator.errors)
    return sensor_validator.normalized(sens_conf)


def initialise_sensor_input(sens_conf, sensor):
    """
    Initialises sensor input.
    :param sens_conf: Sensor config
    :type sens_conf: dict
    :param sensor: Instance of GenericSensor to use
    :type sensor: pi_mqtt_gpio.modules.GenericSensor
    :return: None
    :rtype: NoneType
    """
    sensor.setup_sensor(sens_conf)


def sensor_timer_thread(SENSOR_MODULES, sensor_inputs, topic_prefix):
    """
    Timer thread for the sensors
    To reduce cpu usage, there is only one cyclic thread for all sensors.
    At the beginning the cycle time is calculated (ggT) to match all intervals.
    For each sensor interval, the reduction value is calculated, that triggers
    the read, round and publish for the sensor, when loop_count is a multiple
    of it. In worst case, the cycle_time is 1 second, in best case, e.g., when
    there is only one sensor, cycle_time is its interval.
    """
    # calculate the min time
    arr = []
    for sens_conf in sensor_inputs:
        arr.append(sens_conf.get("interval", 60))

    # get the greatest common divisor (gcd) for the list of interval times
    cycle_time = reduce(lambda x, y: gcd(x, y), arr)

    _LOG.debug(
        "sensor_timer_thread: calculated cycle_time will be %d seconds", cycle_time
    )

    for sens_conf in sensor_inputs:
        sens_conf["interval_reduction"] = sens_conf.get("interval", 60) / cycle_time

    # Start the cyclic thread
    loop_count = 0
    next_call = time()
    while True:
        loop_count += 1
        for sens_conf in sensor_inputs:
            if loop_count % sens_conf["interval_reduction"] == 0:
                sensor = SENSOR_MODULES[sens_conf["module"]]

                try:
                    value = sensor.get_value(sens_conf)
                    if value is None:
                        _LOG.warning(
                            "sensor_timer_thread: sensor %r returned null",
                            sens_conf["name"],
                        )
                        continue
                    value = round(value, sens_conf["digits"])

                    _LOG.info(
                        "sensor_timer_thread: reading sensor '%s' value %r",
                        sens_conf["name"],
                        value,
                    )

                    # publish each value
                    client.publish(
                        "%s/%s/%s" % (topic_prefix, SENSOR_TOPIC, sens_conf["name"]),
                        payload=value,
                        retain=sens_conf["retain"],
                    )
                except ModuleConfigInvalid as exc:
                    _LOG.error(
                        "sensor_timer_thread: failed to read sensor '%s': %s",
                        sens_conf["name"],
                        exc,
                    )

        # schedule next call
        next_call = next_call + cycle_time  # every cycle_time sec
        sleep(max(0, next_call - time()))


def validate_stream_read_config(stream_conf):
    """
    Validates stream read config.
    :param stream_conf: Stream read config
    :type stream_conf: dict
    :return: None
    :rtype: NoneType
    """
    stream_module = import_module(
        "pi_mqtt_gpio.modules.%s" % STREAM_CONFIGS[stream_conf["module"]]["module"]
    )
    # Doesn't need to be a deep copy because we won't modify the base
    # validation rules, just add more of them.
    stream_read_schema = CONFIG_SCHEMA["stream_reads"]["schema"]["schema"].copy()
    stream_read_schema.update(getattr(stream_module, "STREAM_SCHEMA", {}))
    stream_validator = cerberus.Validator(stream_read_schema)
    if not stream_validator.validate(stream_conf):
        raise ModuleConfigInvalid(stream_validator.errors)
    return stream_validator.normalized(stream_conf)


def validate_stream_write_config(stream_conf):
    """
    Validates stream write config.
    :param stream_conf: Stream write config
    :type stream_conf: dict
    :return: None
    :rtype: NoneType
    """
    stream_module = import_module(
        "pi_mqtt_gpio.modules.%s" % STREAM_CONFIGS[stream_conf["module"]]["module"]
    )
    # Doesn't need to be a deep copy because we won't modify the base
    # validation rules, just add more of them.
    stream_write_schema = CONFIG_SCHEMA["stream_writes"]["schema"]["schema"].copy()
    stream_write_schema.update(getattr(stream_module, "STREAM_SCHEMA", {}))
    stream_validator = cerberus.Validator(stream_write_schema)
    if not stream_validator.validate(stream_conf):
        raise ModuleConfigInvalid(stream_validator.errors)
    return stream_validator.normalized(stream_conf)


def initialise_stream(stream_conf, stream):
    """
    Initialises stream.
    :param stream_conf: Stream config
    :type stream_conf: dict
    :param stream: Instance of GenericStream to use
    :type stream: pi_mqtt_gpio.modules.GenericStream
    :return: None
    :rtype: NoneType
    """
    stream.setup_stream(stream_conf)


def stream_timer_thread(STREAM_MODULES, stream_reads, topic_prefix):
    """
    Timer thread for the stream reads
    To reduce cpu usage, there is only one cyclic thread for all streams.
    At the beginning the cycle time is calculated (ggT) to match all intervals.
    For each stream interval, the reduction value is calculated, that triggers
    the read, round and publish for the stream, when loop_count is a multiple
    of it. In worst case, the cycle_time is 1 second, in best case, e.g., when
    there is only one stream, cycle_time is its interval.
    """
    # calculate the min time
    arr = []
    for stream_conf in stream_reads:
        arr.append(stream_conf.get("interval", 60))

    # get the greatest common divisor (gcd) for the list of interval times
    cycle_time = reduce(lambda x, y: gcd(x, y), arr)

    _LOG.debug(
        "stream_timer_thread: calculated cycle_time will be %d seconds", cycle_time
    )

    for stream_conf in stream_reads:
        stream_conf["interval_reduction"] = stream_conf.get("interval", 60) / cycle_time

    # Start the cyclic thread
    loop_count = 0
    next_call = time()
    while True:
        loop_count += 1
        for stream_conf in stream_reads:
            if loop_count % stream_conf["interval_reduction"] == 0:
                stream = STREAM_MODULES[stream_conf["module"]]

                try:
                    data = stream.read(stream_conf)
                    if data is None:
                        continue
                    if len(data) == 0:
                        continue

                    _LOG.info(
                        "stream_timer_thread: reading stream '%s' data %s",
                        stream_conf["name"],
                        data,
                    )
                    client.publish(
                        "%s/%s/%s" % (topic_prefix, STREAM_TOPIC, stream_conf["name"]),
                        payload=data,
                        retain=stream_conf["retain"],
                    )
                except ModuleConfigInvalid as exc:
                    _LOG.error(
                        "stream_timer_thread: failed to read stream '%s': %s",
                        stream_conf["name"],
                        exc,
                    )

        # schedule next call
        next_call = next_call + cycle_time  # every cycle_time sec
        sleep(max(0, next_call - time()))


def gpio_interrupt_callback(module, pin):
    try:
        in_conf = GPIO_INTERRUPT_LOOKUP[module][pin]
    except KeyError as exc:
        _LOG.error(
            "gpio_interrupt_callback: no interrupt configured \
            for pin '%s' on module %s: %s",
            pin,
            module,
            exc,
        )
    _LOG.info("Interrupt: Input %r triggered", in_conf["name"])

    # publish the interrupt trigger
    client.publish(
        "%s/%s/%s" % (topic_prefix, INPUT_TOPIC, in_conf["name"]),
        payload=in_conf["interrupt_payload"],
        retain=in_conf["retain"],
    )


def hass_announce_digital_input(in_conf, topic_prefix, mqtt_config):
    """
    Announces digital input as binary_sensor to HomeAssistant.
    :param in_conf: Input config
    :type in_conf: dict
    :return: None
    :rtype: NoneType
    """
    device_id = (
        "pi-mqtt-gpio-%s" % sha1(topic_prefix.encode("utf8")).hexdigest()[:8]
    )  # TODO: Unify with MQTT Client ID
    sensor_name = in_conf["name"]
    sensor_config = {
        "name": sensor_name,
        "unique_id": "%s_%s_input_%s" % (device_id, in_conf["module"], sensor_name),
        "state_topic": "%s/%s/%s" % (topic_prefix, INPUT_TOPIC, in_conf["name"]),
        "availability_topic": "%s/%s" % (topic_prefix, mqtt_config["status_topic"]),
        "payload_available": mqtt_config["status_payload_running"],
        "payload_not_available": mqtt_config["status_payload_dead"],
        "payload_on": in_conf["on_payload"],
        "payload_off": in_conf["off_payload"],
        "device": {
            "manufacturer": "MQTT GPIO",
            "identifiers": ["mqtt-gpio", device_id],
            "name": mqtt_config["discovery_name"],
        },
    }

    client.publish(
        "%s/%s/%s/%s/config"
        % (mqtt_config["discovery_prefix"], in_conf. get("component", "binary_sensor"), device_id, sensor_name),
        payload=json.dumps(sensor_config),
        retain=True,
    )


def hass_announce_digital_output(out_conf, topic_prefix, mqtt_config):
    """
    Announces digital output as switch to HomeAssistant.
    :param out_conf: Output config
    :type out_conf: dict
    :return: None
    :rtype: NoneType
    """
    device_id = (
        "pi-mqtt-gpio-%s" % sha1(topic_prefix.encode("utf8")).hexdigest()[:8]
    )  # TODO: Unify with MQTT Client ID
    sensor_name = out_conf["name"]
    sensor_config = {
        "name": sensor_name,
        "unique_id": "%s_%s_output_%s" % (device_id, out_conf["module"], sensor_name),
        "state_topic": "%s/%s/%s" % (topic_prefix, OUTPUT_TOPIC, out_conf["name"]),
        "command_topic": "%s/%s/%s/%s"
        % (topic_prefix, OUTPUT_TOPIC, out_conf["name"], SET_TOPIC),
        "availability_topic": "%s/%s" % (topic_prefix, mqtt_config["status_topic"]),
        "payload_available": mqtt_config["status_payload_running"],
        "payload_not_available": mqtt_config["status_payload_dead"],
        "payload_on": out_conf["on_payload"],
        "payload_off": out_conf["off_payload"],
        "device": {
            "manufacturer": "MQTT GPIO",
            "identifiers": ["mqtt-gpio", device_id],
            "name": mqtt_config["discovery_name"],
        },
    }

    client.publish(
        "%s/%s/%s/%s/config"
        % (mqtt_config["discovery_prefix"], out_conf. get("component", "switch"), device_id, sensor_name),
        payload=json.dumps(sensor_config),
        retain=True,
    )


def hass_announce_sensor_input(in_conf, topic_prefix, mqtt_config):
    """
    Announces digital output as sensor to HomeAssistant.
    :param in_conf: Input config
    :type in_conf: dict
    :return: None
    :rtype: NoneType
    """
    device_id = (
        "pi-mqtt-gpio-%s" % sha1(topic_prefix.encode("utf8")).hexdigest()[:8]
    )  # TODO: Unify with MQTT Client ID
    sensor_name = in_conf["name"]
    sensor_config = {
        "name": sensor_name,
        "unique_id": "%s_%s_output_%s" % (device_id, in_conf["module"], sensor_name),
        "state_topic": "%s/%s/%s" % (topic_prefix, SENSOR_TOPIC, in_conf["name"]),
        "availability_topic": "%s/%s" % (topic_prefix, mqtt_config["status_topic"]),
        "payload_available": mqtt_config["status_payload_running"],
        "payload_not_available": mqtt_config["status_payload_dead"],
        "expire_after": 2 * int(in_conf.get("interval", "60")) + 5,
        "device": {
            "manufacturer": "MQTT GPIO",
            "identifiers": ["mqtt-gpio", device_id],
            "name": mqtt_config["discovery_name"],
        },
    }
    if "unit_of_measurement" in in_conf:
        sensor_config["unit_of_measurement"] = in_conf["unit_of_measurement"]

    client.publish(
        "%s/%s/%s/%s/config"
        % (mqtt_config["discovery_prefix"], in_conf.get("component", "sensor"), device_id, sensor_name),
        payload=json.dumps(sensor_config),
        retain=True,
    )


def main(args):
    global digital_inputs
    global digital_outputs
    global sensor_inputs
    global stream_writes
    global client
    global scheduler

    _LOG.info("Startup")

    with open(args.config) as f:
        config = yaml.safe_load(f)
    validator = ConfigValidator(CONFIG_SCHEMA)
    if not validator.validate(config):
        _LOG.error("Config did not validate:\n%s", yaml.dump(validator.errors))
        sys.exit(1)
    config = validator.normalized(config)

    # Remove all handlers associated with the root logger object.
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    # and load the new config from the config file
    logging.config.dictConfig(config["logging"])

    digital_inputs = config["digital_inputs"]
    digital_outputs = config["digital_outputs"]
    sensor_inputs = config["sensor_inputs"]
    stream_reads = config["stream_reads"]
    stream_writes = config["stream_writes"]

    client = init_mqtt(config["mqtt"], config["digital_outputs"], config["stream_writes"])
    topic_prefix = config["mqtt"]["topic_prefix"]

    # Install modules for GPIOs
    for gpio_config in config["gpio_modules"]:
        GPIO_CONFIGS[gpio_config["name"]] = gpio_config
        try:
            GPIO_MODULES[gpio_config["name"]] = configure_gpio_module(gpio_config)
        except ModuleConfigInvalid as exc:
            _LOG.error(
                "Config for %r module named %r did not validate:\n%s",
                gpio_config["module"],
                gpio_config["name"],
                yaml.dump(exc.errors),
            )
            sys.exit(1)

    # Install modules for Sensors
    for sensor_config in config.get("sensor_modules", {}):
        SENSOR_CONFIGS[sensor_config["name"]] = sensor_config
        try:
            SENSOR_MODULES[sensor_config["name"]] = configure_sensor_module(sensor_config)
        except ModuleConfigInvalid as exc:
            _LOG.error(
                "Config for %r module named %r did not validate:\n%s",
                sensor_config["module"],
                sensor_config["name"],
                yaml.dump(exc.errors),
            )
            sys.exit(1)

    # Install modules for Streams
    for stream_config in config.get("stream_modules", {}):
        STREAM_CONFIGS[stream_config["name"]] = stream_config
        try:
            STREAM_MODULES[stream_config["name"]] = configure_stream_module(stream_config)
        except ModuleConfigInvalid as exc:
            _LOG.error(
                "Config for %r module named %r did not validate:\n%s",
                stream_config["module"],
                stream_config["name"],
                yaml.dump(exc.errors),
            )
            sys.exit(1)

    for in_conf in digital_inputs:
        initialise_digital_input(in_conf, GPIO_MODULES[in_conf["module"]])
        LAST_STATES[in_conf["name"]] = None

    for out_conf in digital_outputs:
        initialise_digital_output(out_conf, GPIO_MODULES[out_conf["module"]])

    for sens_conf in sensor_inputs:
        try:
            SENSOR_INPUT_CONFIGS[sens_conf["name"]] = validate_sensor_input_config(
                sens_conf
            )
        except ModuleConfigInvalid as exc:
            _LOG.error(
                "Config for %r sensor named %r did not validate:\n%s",
                SENSOR_CONFIGS[sens_conf["module"]]["module"],
                sens_conf["name"],
                yaml.dump(exc.errors),
            )
            sys.exit(1)
        initialise_sensor_input(sens_conf, SENSOR_MODULES[sens_conf["module"]])

    for stream_conf in stream_reads:
        try:
            STREAM_READ_CONFIGS[stream_conf["name"]] = validate_stream_read_config(
                stream_conf
            )
        except ModuleConfigInvalid as exc:
            _LOG.error(
                "Config for %r stream named %r did not validate:\n%s",
                STREAM_CONFIGS[stream_conf["module"]]["module"],
                stream_conf["name"],
                yaml.dump(exc.errors),
            )
            sys.exit(1)
        initialise_stream(stream_conf, STREAM_MODULES[stream_conf["module"]])

    for stream_conf in stream_writes:
        try:
            STREAM_WRITE_CONFIGS[stream_conf["name"]] = validate_stream_write_config(
                stream_conf
            )
        except ModuleConfigInvalid as exc:
            _LOG.error(
                "Config for %r stream named %r did not validate:\n%s",
                STREAM_CONFIGS[stream_conf["module"]]["module"],
                stream_conf["name"],
                yaml.dump(exc.errors),
            )
            sys.exit(1)
        initialise_stream(stream_conf, STREAM_MODULES[stream_conf["module"]])

    try:
        client.connect(
            config["mqtt"]["host"], config["mqtt"]["port"], config["mqtt"]["keepalive"]
        )
    except socket.error as err:
        _LOG.fatal("Unable to connect to MQTT server: %s" % err)
        sys.exit(1)
    client.loop_start()

    for out_conf in digital_outputs:
        # If configured to do so, publish the initial states of the outputs
        initial_setting = out_conf.get("initial")
        if initial_setting is not None and out_conf.get("publish_initial", False):
            payload = out_conf[
                "on_payload" if initial_setting == "high" else "off_payload"
            ]
            client.publish(
                "%s/%s/%s" % (topic_prefix, OUTPUT_TOPIC, out_conf["name"]),
                retain=out_conf["retain"],
                payload=payload,
            )

    scheduler = Scheduler()

    try:
        # Starting the sensor thread (if there are sensors configured)
        if sensor_inputs:
            sensor_thread = threading.Thread(
                target=sensor_timer_thread,
                kwargs={
                    "SENSOR_MODULES": SENSOR_MODULES,
                    "sensor_inputs": SENSOR_INPUT_CONFIGS.values(),
                    "topic_prefix": topic_prefix,
                },
            )
            sensor_thread.name = "pi-mqtt-gpio_SensorReader"
            # stops the thread, when main program terminates
            sensor_thread.daemon = True
            sensor_thread.start()

        # Starting the stream thread (if there are streams configured)
        if stream_reads:
            stream_thread = threading.Thread(
                target=stream_timer_thread,
                kwargs={
                    "STREAM_MODULES": STREAM_MODULES,
                    "stream_reads": STREAM_READ_CONFIGS.values(),
                    "topic_prefix": topic_prefix,
                },
            )
            stream_thread.name = "pi-mqtt-gpio_StreamReader"
            # stops the thread, when main program terminates
            stream_thread.daemon = True
            stream_thread.start()

        while True:
            for in_conf in digital_inputs:
                # Only read pins that are not configured as interrupt.
                # Read interrupts once at startup (startup_read)
                if in_conf["interrupt"] != "none":
                    continue
                gpio = GPIO_MODULES[in_conf["module"]]
                state = get_pin(in_conf, gpio)
                sleep(0.01)
                if get_pin(in_conf, gpio) != state:
                    continue
                if state != LAST_STATES[in_conf["name"]]:
                    _LOG.info(
                        "Polling: Input %r state changed to %r", in_conf["name"], state
                    )
                    client.publish(
                        "%s/%s/%s" % (topic_prefix, INPUT_TOPIC, in_conf["name"]),
                        payload=(
                            in_conf["on_payload"] if state else in_conf["off_payload"]
                        ),
                        retain=in_conf["retain"],
                    )
                    LAST_STATES[in_conf["name"]] = state
            scheduler.loop()
            sleep(0.01)
    except KeyboardInterrupt:
        print("")
    finally:
        client.publish(
            "%s/%s" % (topic_prefix, config["mqtt"]["status_topic"]),
            config["mqtt"]["status_payload_stopped"],
            qos=1,
            retain=True,
        )

        client.loop_stop()
        client.disconnect()
        client.loop_forever()

        for name, gpio in GPIO_MODULES.items():
            if not GPIO_CONFIGS[name]["cleanup"]:
                _LOG.info("Cleanup disabled for module %r.", name)
                continue
            try:
                gpio.cleanup()
            except Exception:
                _LOG.exception("Unable to execute cleanup routine for module %r:", name)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG, format="%(asctime)s %(name)s (%(levelname)s): %(message)s"
    )

    p = argparse.ArgumentParser()
    p.add_argument("config")
    args = p.parse_args()
    main(args)
