import argparse
import logging
import logging.config
import yaml
import sys
import socket
import ssl
from time import sleep, time
from importlib import import_module
from hashlib import sha1

import threading  # For callback functions
from fractions import gcd  # for calculating the callback periodic time
from functools import reduce

import paho.mqtt.client as mqtt
import cerberus

from pi_mqtt_gpio import CONFIG_SCHEMA
from pi_mqtt_gpio.modules import PinPullup, PinDirection, InterruptEdge, \
                                 BASE_SCHEMA
from pi_mqtt_gpio.scheduler import Scheduler, Task


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
GPIO_CONFIGS = {}  # storage for gpios
SENSOR_CONFIGS = {}  # storage for sensors
SENSOR_INPUT_CONFIGS = {}  # storage for sensor input configs
LAST_STATES = {}
GPIO_INTERRUPT_LOOKUP = {}
SET_TOPIC = "set"
SET_ON_MS_TOPIC = "set_on_ms"
SET_OFF_MS_TOPIC = "set_off_ms"
OUTPUT_TOPIC = "output"
INPUT_TOPIC = "input"
SENSOR_TOPIC = "sensor"

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
    scheduler.add_task(Task(time() + ms / 1000.0, set_pin, topic_prefix, output_config, not value))
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
    scheduler.add_task(Task(time() + ms / 1000.0, set_pin, topic_prefix, output_config, not value))
    _LOG.info(
        "Scheduled output %r to change back to %r after %r ms.",
        output_config["name"],
        not value,
        ms,
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
        _LOG.info("Module %r has no extra requirements to install.", module)
        return
    import pkg_resources

    pkgs_installed = pkg_resources.WorkingSet()
    pkgs_required = []
    for req in reqs:
        if pkgs_installed.find(pkg_resources.Requirement.parse(req)) is None:
            pkgs_required.append(req)
    if pkgs_required:
        from subprocess import check_call, CalledProcessError

        try:
            check_call(["/usr/bin/env", "pip", "install"] + pkgs_required)
        except CalledProcessError as err:
            raise CannotInstallModuleRequirements(
                "Unable to install packages for module %r (%s): %s"
                % (module, pkgs_required, err)
            )


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
    _LOG.debug(
        "Last will set on %r as %r.", status_topic, config["status_payload_dead"]
    )

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
            client.publish(
                status_topic, config["status_payload_running"], qos=1, retain=True
            )
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
            _LOG.info("Received message on topic %r: %r", msg.topic, msg.payload)
            if msg.topic.endswith("/%s" % SET_TOPIC):
                handle_set(topic_prefix, msg)
            elif msg.topic.endswith("/%s" % SET_ON_MS_TOPIC):
                handle_set_ms(topic_prefix, msg, True)
            elif msg.topic.endswith("/%s" % SET_OFF_MS_TOPIC):
                handle_set_ms(topic_prefix, msg, False)
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
                "both": InterruptEdge.BOTH
            }[in_conf["interrupt"]]
        except KeyError as exc:
            _LOG.error(
                "initialise_digital_input: config value(%s) for 'interrupt' \
                 invalid in  entry '%s'",
                in_conf["interrupt"],
                in_conf["name"]
            )

        try:
            bouncetime = in_conf["bouncetime"]
            module = in_conf["module"]
            gpio.setup_interrupt(
                module, pin, edge, gpio_interrupt_callback, bouncetime)

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
                exc
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


def gpio_interrupt_callback(module, pin):
    try:
        in_conf = GPIO_INTERRUPT_LOOKUP[module][pin]
    except KeyError as exc:
        _LOG.error(
            "gpio_interrupt_callback: no interrupt configured \
            for pin '%s' on module %s: %s",
            pin,
            module,
            exc
        )
    _LOG.info("Interrupt: Input %r triggered", in_conf["name"])
    
    # publish the interrupt trigger
    client.publish(
        "%s/%s/%s" % (topic_prefix, INPUT_TOPIC, in_conf["name"]),
        payload=in_conf["interrupt_payload"],
        retain=in_conf["retain"],
    )


def main(args):
    global digital_outputs
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

    client = init_mqtt(config["mqtt"], config["digital_outputs"])

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
            SENSOR_MODULES[sensor_config["name"]] = configure_sensor_module(
                sensor_config
            )
        except ModuleConfigInvalid as exc:
            _LOG.error(
                "Config for %r module named %r did not validate:\n%s",
                sensor_config["module"],
                sensor_config["name"],
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

    try:
        client.connect(config["mqtt"]["host"], config["mqtt"]["port"], 60)
    except socket.error as err:
        _LOG.fatal("Unable to connect to MQTT server: %s" % err)
        sys.exit(1)
    client.loop_start()

    scheduler = Scheduler()

    topic_prefix = config["mqtt"]["topic_prefix"]
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

        while True:
            for in_conf in digital_inputs:
                # only read pins, that are not configured as interrupt. Read interrupts once at startup (startup_read)
                if (in_conf["interrupt"] == "none"):
                    gpio = GPIO_MODULES[in_conf["module"]]
                    state = bool(gpio.get_pin(in_conf["pin"]))
                    sleep(0.01)
                    if bool(gpio.get_pin(in_conf["pin"])) != state:
                        continue
                    if state != LAST_STATES[in_conf["name"]]:
                        _LOG.info("Polling: Input %r state changed to %r", in_conf["name"], state)
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
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(name)s (%(levelname)s): %(message)s')

    p = argparse.ArgumentParser()
    p.add_argument("config")
    args = p.parse_args()
    main(args)