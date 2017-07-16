import argparse
import logging
import yaml
import json
import sys
from time import sleep
from importlib import import_module

import paho.mqtt.client as mqtt
import cerberus

from pi_mqtt_gpio.modules import PinPullup, PinDirection


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
    def _normalize_coerce_rstrip_slash(self, value):
        return value.rstrip("/")


def on_disconnect(client, userdata, rc):
    _LOG.warning("Disconnected from MQTT server with code: %s" % rc)
    while rc != 0:
        sleep(RECONNECT_DELAY_SECS)
        rc = client.reconnect()


def install_missing_requirements(module):
    """
    Some of the modules require external packages to be installed. This gets
    the list from the `REQUIREMENTS` module attribute and attempts to
    install the requirements using pip.
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
    :param topic: str such as mytopicprefix/output/tv_lamp/set
    :param topic_prefix: str prefix of our topics
    :return: str name of the output this topic is setting
    """
    if not topic.endswith("/%s" % SET_TOPIC):
        raise ValueError("This topic does not end with '/%s'" % SET_TOPIC)
    lindex = len("%s/%s/" % (topic_prefix, OUTPUT_TOPIC))
    rindex = -len(SET_TOPIC)-1
    return topic[lindex:rindex]


def init_mqtt(config):
    """
    Configure MQTT client.
    """
    client = mqtt.Client()
    user = config["mqtt"].get("user")
    password = config["mqtt"].get("password")
    topic_prefix = config["mqtt"]["topic_prefix"]

    if user and password:
        client.username_pw_set(user, password)

    def on_conn(client, userdata, flags, rc):
        for output_config in config.get("digital_outputs", []):
            topic = "%s/%s/%s/%s" % (
                topic_prefix, OUTPUT_TOPIC, output_config["name"], SET_TOPIC)
            client.subscribe(topic, qos=1)
            _LOG.info("Subscribed to topic: %r", topic)

    def on_msg(client, userdata, msg):
        _LOG.info("Received message on topic %r: %r", msg.topic, msg.payload)
        output_name = output_name_from_topic_set(msg.topic, topic_prefix)
        output_config = None
        for output in config.get("digital_outputs", []):
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
            json.dumps(validator.errors, indent=2))
        sys.exit(1)
    config = validator.normalized(config)

    client = init_mqtt(config)

    for gpio_config in config["gpio_modules"]:
        gpio_module = import_module(
            "pi_mqtt_gpio.modules.%s" % gpio_config["module"])
        install_missing_requirements(gpio_module)
        GPIOS[gpio_config["name"]] = gpio_module.GPIO(gpio_config)

    for input_config in config.get("digital_inputs", []):
        pud = None
        if input_config["pullup"]:
            pud = PinPullup.UP
        elif input_config["pulldown"]:
            pud = PinPullup.DOWN

        gpio = GPIOS[input_config["module"]]
        gpio.setup_pin(
            input_config["pin"], PinDirection.INPUT, pud, input_config)
        LAST_STATES[input_config["name"]] = None

    for output_config in config.get("digital_outputs", []):
        gpio = GPIOS[output_config["module"]]
        gpio.setup_pin(
            output_config["pin"], PinDirection.OUTPUT, None, output_config)

    client.connect(config["mqtt"]["host"], config["mqtt"]["port"], 60)
    client.loop_start()

    topic_prefix = config["mqtt"]["topic_prefix"]
    try:
        while True:
            for input_config in config.get("digital_inputs", []):
                gpio = GPIOS[input_config["module"]]
                state = bool(gpio.get_pin(input_config["pin"]))
                sleep(0.05)
                if bool(gpio.get_pin(input_config["pin"])) != state:
                    continue
                if state != LAST_STATES[input_config["name"]]:
                    _LOG.info(
                        "Input %r state changed to %r",
                        input_config["name"],
                        state)
                    client.publish(
                        "%s/input/%s" % (topic_prefix, input_config["name"]),
                        payload=(input_config["on_payload"] if state
                                 else input_config["off_payload"]))
                    LAST_STATES[input_config["name"]] = state
            sleep(0.05)
    except KeyboardInterrupt:
        print("")
    finally:
        client.disconnect()
        client.loop_stop()
