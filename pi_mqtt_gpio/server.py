import argparse
import logging
import yaml
import sys
import socket
from time import sleep, time
from importlib import import_module
from hashlib import sha1

import paho.mqtt.client as mqtt
import cerberus

from pi_mqtt_gpio import CONFIG_SCHEMA
from pi_mqtt_gpio.modules import PinPullup, PinDirection, BASE_SCHEMA
from pi_mqtt_gpio.scheduler import Scheduler, Task


LOG_LEVEL_MAP = {
    mqtt.MQTT_LOG_INFO: logging.INFO,
    mqtt.MQTT_LOG_NOTICE: logging.INFO,
    mqtt.MQTT_LOG_WARNING: logging.WARNING,
    mqtt.MQTT_LOG_ERR: logging.ERROR,
    mqtt.MQTT_LOG_DEBUG: logging.DEBUG
}
RECONNECT_DELAY_SECS = 5
GPIO_MODULES = {}
GPIO_CONFIGS = {}
LAST_STATES = {}
SET_TOPIC = "set"
SET_ON_MS_TOPIC = "set_on_ms"
SET_OFF_MS_TOPIC = "set_off_ms"
OUTPUT_TOPIC = "output"
INPUT_TOPIC = "input"

_LOG = logging.getLogger(__name__)
_LOG.addHandler(logging.StreamHandler())
_LOG.setLevel(logging.DEBUG)


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


def set_pin(output_config, value):
    """
    Sets the output pin to a new value and publishes it on MQTT.
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
        set_value)
    payload = output_config["on_payload" if value else "off_payload"]
    client.publish(
        "%s/%s/%s" % (topic_prefix, OUTPUT_TOPIC, output_config["name"]),
        retain=output_config["retain"],
        payload=payload)


def handle_set(msg):
    """
    Handles an incoming 'set' MQTT message.
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
    if payload not in (
            output_config["on_payload"], output_config["off_payload"]):
        _LOG.warning(
            "Payload %r does not relate to configured on/off values %r and %r",
            payload,
            output_config["on_payload"],
            output_config["off_payload"])
        return
    set_pin(output_config, payload == output_config["on_payload"])


def handle_set_ms(msg, value):
    """
    Handles an incoming 'set_<on/off>_ms' MQTT message.
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
        raise InvalidPayload(
            "Could not parse ms value %r to an integer." % msg.payload)
    suffix = SET_ON_MS_TOPIC if value else SET_OFF_MS_TOPIC
    output_name = output_name_from_topic(msg.topic, topic_prefix, suffix)
    output_config = output_by_name(output_name)
    if output_config is None:
        return

    set_pin(output_config, value)
    scheduler.add_task(Task(
        time() + ms/1000.0,
        set_pin,
        output_config,
        not value
    ))
    _LOG.info(
        "Scheduled output %r to change back to %r after %r ms.",
        output_config["name"],
        not value,
        ms
    )


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
        _LOG.info("Module %r has no extra requirements to install." % module)
        return
    import pkg_resources
    pkgs_installed = pkg_resources.WorkingSet()
    pkgs_required = []
    for req in reqs:
        if pkgs_installed.find(pkg_resources.Requirement.parse(req)) is None:
            pkgs_required.append(req)
    if pkgs_required:
        from pip.commands.install import InstallCommand
        from pip.status_codes import SUCCESS
        cmd = InstallCommand()
        result = cmd.main(pkgs_required)
        if result != SUCCESS:
            raise CannotInstallModuleRequirements(
                "Unable to install packages for module %r (%s)..." % (
                    module, pkgs_required))


def output_name_from_topic(topic, topic_prefix, suffix):
    """
    Return the name of the output which the topic is setting.
    :param topic: String such as 'mytopicprefix/output/tv_lamp/set'
    :type topic: str
    :param topic_prefix: Prefix of our topics
    :type topic_prefix: str
    :param suffix: The suffix of the topic such as "set" or "set_ms"
    :type suffix: str
    :return: Name of the output this topic is setting
    :rtype: str
    """
    if not topic.endswith("/%s" % suffix):
        raise ValueError("This topic does not end with '/%s'" % suffix)
    lindex = len("%s/%s/" % (topic_prefix, OUTPUT_TOPIC))
    rindex = -len(suffix)-1
    return topic[lindex:rindex]


def init_mqtt(config, digital_outputs):
    """
    Configure MQTT client.
    :param config: Validated config dict containing MQTT connection details
    :type config: dict
    :param digital_outputs: List of validated config dicts for digital outputs
    :type digital_outputs: list
    :return: Connected and initialised MQTT client
    :rtype: paho.mqtt.client.Client
    """
    topic_prefix = config["topic_prefix"]
    protocol = mqtt.MQTTv311
    if config["protocol"] == "3.1":
        protocol = mqtt.MQTTv31

    # https://stackoverflow.com/questions/45774538/what-is-the-maximum-length-of-client-id-in-mqtt
    # TLDR: Soft limit of 23, but we needn't truncate it on our end.
    client_id = config['client_id']
    if not client_id:
        client_id = "pi-mqtt-gpio-%s" % sha1(
            topic_prefix.encode('utf8')).hexdigest()

    client = mqtt.Client(
        client_id=client_id, clean_session=False, protocol=protocol)

    if config["user"] and config["password"]:
        client.username_pw_set(config["user"], config["password"])

    # Set last will and testament (LWT)
    status_topic = "%s/%s" % (topic_prefix, config["status_topic"])
    client.will_set(
        status_topic,
        payload=config["status_payload_dead"],
        qos=1,
        retain=True)
    _LOG.debug(
        "Last will set on %r as %r.",
        status_topic,
        config["status_payload_dead"])

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
                "Connected to the MQTT broker with protocol v%s.",
                config["protocol"])
            for out_conf in digital_outputs:
                for suffix in (SET_TOPIC, SET_ON_MS_TOPIC, SET_OFF_MS_TOPIC):
                    topic = "%s/%s/%s/%s" % (
                        topic_prefix,
                        OUTPUT_TOPIC,
                        out_conf["name"],
                        suffix)
                    client.subscribe(topic, qos=1)
                    _LOG.info("Subscribed to topic: %r", topic)
            client.publish(
                status_topic,
                config["status_payload_running"],
                qos=1,
                retain=True)
        elif rc == 1:
            _LOG.fatal(
                "Incorrect protocol version used to connect to MQTT broker.")
            sys.exit(1)
        elif rc == 2:
            _LOG.fatal(
                "Invalid client identifier used to connect to MQTT broker.")
            sys.exit(1)
        elif rc == 3:
            _LOG.warning("MQTT broker unavailable. Retrying in %s secs...")
            sleep(RECONNECT_DELAY_SECS)
            client.reconnect()
        elif rc == 4:
            _LOG.fatal(
                "Bad username or password used to connect to MQTT broker.")
            sys.exit(1)
        elif rc == 5:
            _LOG.fatal(
                "Not authorised to connect to MQTT broker.")
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
            _LOG.info(
                "Received message on topic %r: %r", msg.topic, msg.payload)
            if msg.topic.endswith("/%s" % SET_TOPIC):
                handle_set(msg)
            elif msg.topic.endswith("/%s" % SET_ON_MS_TOPIC):
                handle_set_ms(msg, True)
            elif msg.topic.endswith("/%s" % SET_OFF_MS_TOPIC):
                handle_set_ms(msg, False)
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
    gpio_module = import_module(
        "pi_mqtt_gpio.modules.%s" % gpio_config["module"])
    # Doesn't need to be a deep copy because we won't modify the base
    # validation rules, just add more of them.
    module_config_schema = BASE_SCHEMA.copy()
    module_config_schema.update(
        getattr(gpio_module, "CONFIG_SCHEMA", {}))
    module_validator = cerberus.Validator(module_config_schema)
    if not module_validator.validate(gpio_config):
        raise ModuleConfigInvalid(module_validator.errors)
    gpio_config = module_validator.normalized(gpio_config)
    install_missing_requirements(gpio_module)
    return gpio_module.GPIO(gpio_config)


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
    pud = None
    if in_conf["pullup"]:
        pud = PinPullup.UP
    elif in_conf["pulldown"]:
        pud = PinPullup.DOWN
    gpio.setup_pin(
        in_conf["pin"], PinDirection.INPUT, pud, in_conf)


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


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("config")
    args = p.parse_args()

    with open(args.config) as f:
        config = yaml.load(f)
    validator = ConfigValidator(CONFIG_SCHEMA)
    if not validator.validate(config):
        _LOG.error(
            "Config did not validate:\n%s",
            yaml.dump(validator.errors))
        sys.exit(1)
    config = validator.normalized(config)

    digital_inputs = config["digital_inputs"]
    digital_outputs = config["digital_outputs"]

    client = init_mqtt(config["mqtt"], config["digital_outputs"])

    for gpio_config in config["gpio_modules"]:
        GPIO_CONFIGS[gpio_config["name"]] = gpio_config
        try:
            GPIO_MODULES[gpio_config["name"]] = configure_gpio_module(
                gpio_config)
        except ModuleConfigInvalid as exc:
            _LOG.error(
                "Config for %r module named %r did not validate:\n%s",
                gpio_config["module"],
                gpio_config["name"],
                yaml.dump(exc.errors)
            )
            sys.exit(1)

    for in_conf in digital_inputs:
        initialise_digital_input(in_conf, GPIO_MODULES[in_conf["module"]])
        LAST_STATES[in_conf["name"]] = None

    for out_conf in digital_outputs:
        initialise_digital_output(out_conf, GPIO_MODULES[out_conf["module"]])

    try:
        client.connect(config["mqtt"]["host"], config["mqtt"]["port"], 60)
    except socket.error as err:
        _LOG.fatal("Unable to connect to MQTT server: %s" % err)
        sys.exit(1)
    client.loop_start()

    scheduler = Scheduler()

    topic_prefix = config["mqtt"]["topic_prefix"]
    try:
        while True:
            for in_conf in digital_inputs:
                gpio = GPIO_MODULES[in_conf["module"]]
                state = bool(gpio.get_pin(in_conf["pin"]))
                sleep(0.01)
                if bool(gpio.get_pin(in_conf["pin"])) != state:
                    continue
                if state != LAST_STATES[in_conf["name"]]:
                    _LOG.info(
                        "Input %r state changed to %r",
                        in_conf["name"],
                        state)
                    client.publish(
                        "%s/%s/%s" % (
                            topic_prefix, INPUT_TOPIC, in_conf["name"]
                        ),
                        payload=(in_conf["on_payload"] if state
                                 else in_conf["off_payload"]),
                        retain=in_conf["retain"]
                    )
                    LAST_STATES[in_conf["name"]] = state
            scheduler.loop()
            sleep(0.01)
    except KeyboardInterrupt:
        print("")
    finally:
        client.publish(
            "%s/%s" % (topic_prefix, config["mqtt"]["status_topic"]),
            config["mqtt"]["status_payload_stopped"], qos=1, retain=True)
        # This should also quit the mqtt loop thread.
        client.disconnect()
        for name, gpio in GPIO_MODULES.items():
            if not GPIO_CONFIGS[name]["cleanup"]:
                _LOG.info("Cleanup disabled for module %r.", name)
                continue
            try:
                gpio.cleanup()
            except Exception:
                _LOG.exception(
                    "Unable to execute cleanup routine for module %r:", name)
