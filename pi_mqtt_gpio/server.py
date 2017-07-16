import argparse
import logging
import yaml
import sys
from time import sleep
from importlib import import_module

import paho.mqtt.client as mqtt
import cerberus

from pi_mqtt_gpio.modules import PinPullup, PinDirection, BASE_SCHEMA


RECONNECT_DELAY_SECS = 5
GPIOS = {}
LAST_STATES = {}
SET_TOPIC = "set"
OUTPUT_TOPIC = "output"
# @TODO: Don't load this at module level
with open("config.schema.yml") as schema:
    CONFIG_SCHEMA = yaml.load(schema)

_LOG = logging.getLogger(__name__)
_LOG.addHandler(logging.StreamHandler())
_LOG.setLevel(logging.DEBUG)


class CannotInstallModuleRequirements(Exception):
    pass


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


def on_disconnect(client, userdata, rc):
    """
    Called when MQTT client disconnects. Attempts to reconnect indefinitely
    if disconnection was unintentional.
    :param client: MQTT client instance
    :param userdata: Any user data set in client
    :param rc: The disconnection result (0 is intentional disconnect)
    :return: None
    :rtype: NoneType
    """
    _LOG.warning("Disconnected from MQTT server with code: %s" % rc)
    while rc != 0:
        sleep(RECONNECT_DELAY_SECS)
        rc = client.reconnect()


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
    reqs = []
    try:
        reqs = getattr(module, "REQUIREMENTS")
    except AttributeError:
        pass
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


def output_name_from_topic_set(topic, topic_prefix):
    """
    Return the name of the output which the topic is setting.
    :param topic: String such as 'mytopicprefix/output/tv_lamp/set'
    :type topic: str
    :param topic_prefix: Prefix of our topics
    :type topic_prefix: str
    :return: Name of the output this topic is setting
    :rtype: str
    """
    if not topic.endswith("/%s" % SET_TOPIC):
        raise ValueError("This topic does not end with '/%s'" % SET_TOPIC)
    lindex = len("%s/%s/" % (topic_prefix, OUTPUT_TOPIC))
    rindex = -len(SET_TOPIC)-1
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
    client = mqtt.Client()
    topic_prefix = config["topic_prefix"]

    if config["user"] and config["password"]:
        client.username_pw_set(config["user"], config["password"])

    def on_conn(client, *args, **kwargs):
        """
        On connection to MQTT, subscribe to the relevant topics.
        :param client: Connected MQTT client instance
        :type client: paho.mqtt.client.Client
        :return: None
        :rtype: NoneType
        """
        for out_conf in digital_outputs:
            topic = "%s/%s/%s/%s" % (
                topic_prefix, OUTPUT_TOPIC, out_conf["name"], SET_TOPIC)
            client.subscribe(topic, qos=1)
            _LOG.info("Subscribed to topic: %r", topic)

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
        _LOG.info("Received message on topic %r: %r", msg.topic, msg.payload)
        output_name = output_name_from_topic_set(msg.topic, topic_prefix)
        output_config = None
        for output in digital_outputs:
            if output["name"] == output_name:
                output_config = output
                break
        if output_config is None:
            _LOG.warning("No output found with name of %r", output_name)
            return
        if msg.payload not in (
                output_config["on_payload"], output_config["off_payload"]):
            _LOG.warning(
                "Payload does not relate to configured on/off values: %r",
                msg.payload)
            return
        value = msg.payload == output_config["on_payload"]
        gpio = GPIOS[output_config["module"]]
        gpio.set_pin(output_config["pin"], value)
        _LOG.info(
            "Set %r output %r to %r",
            output_config["module"],
            output_config["name"],
            value)
        client.publish(
            "%s/%s/%s" % (topic_prefix, OUTPUT_TOPIC, output_name),
            payload=msg.payload)

    client.on_disconnect = on_disconnect
    client.on_connect = on_conn
    client.on_message = on_msg

    return client


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

    client = init_mqtt(config["mqtt"], config["output_config"])

    for gpio_config in config["gpio_modules"]:
        gpio_module = import_module(
            "pi_mqtt_gpio.modules.%s" % gpio_config["module"])
        # Doesn't need to be a deep copy because we won't modify the base
        # validation rules, just add more of them.
        module_config_schema = BASE_SCHEMA.copy()
        module_config_schema.update(
            getattr(gpio_module, "CONFIG_SCHEMA", {}))
        module_validator = cerberus.Validator(module_config_schema)
        if not module_validator.validate(gpio_config):
            _LOG.error(
                "Config for %r module named %r did not validate:\n%s",
                gpio_config["module"],
                gpio_config["name"],
                yaml.dump(module_validator.errors)
            )
            sys.exit(1)
        gpio_config = module_validator.normalized(gpio_config)
        install_missing_requirements(gpio_module)
        GPIOS[gpio_config["name"]] = gpio_module.GPIO(gpio_config)

    for in_conf in digital_inputs:
        pud = None
        if in_conf["pullup"]:
            pud = PinPullup.UP
        elif in_conf["pulldown"]:
            pud = PinPullup.DOWN

        gpio = GPIOS[in_conf["module"]]
        gpio.setup_pin(
            in_conf["pin"], PinDirection.INPUT, pud, in_conf)
        LAST_STATES[in_conf["name"]] = None

    for out_conf in digital_outputs:
        gpio = GPIOS[out_conf["module"]]
        gpio.setup_pin(
            out_conf["pin"], PinDirection.OUTPUT, None, out_conf)

    client.connect(config["mqtt"]["host"], config["mqtt"]["port"], 60)
    client.loop_start()

    topic_prefix = config["mqtt"]["topic_prefix"]
    try:
        while True:
            for in_conf in digital_inputs:
                gpio = GPIOS[in_conf["module"]]
                state = bool(gpio.get_pin(in_conf["pin"]))
                sleep(0.05)
                if bool(gpio.get_pin(in_conf["pin"])) != state:
                    continue
                if state != LAST_STATES[in_conf["name"]]:
                    _LOG.info(
                        "Input %r state changed to %r",
                        in_conf["name"],
                        state)
                    client.publish(
                        "%s/input/%s" % (topic_prefix, in_conf["name"]),
                        payload=(in_conf["on_payload"] if state
                                 else in_conf["off_payload"]))
                    LAST_STATES[in_conf["name"]] = state
            sleep(0.05)
    except KeyboardInterrupt:
        print("")
    finally:
        client.disconnect()
        client.loop_stop()
