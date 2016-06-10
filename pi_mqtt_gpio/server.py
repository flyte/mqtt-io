import argparse
import logging
import yaml
from time import sleep

import RPi.GPIO as gpio
import paho.mqtt.client as mqtt


RECONNECT_DELAY_SECS = 5

_LOG = logging.getLogger(__name__)
_LOG.addHandler(logging.StreamHandler())
_LOG.setLevel(logging.DEBUG)


def on_disconnect(client, userdata, rc):
    _LOG.warning("Disconnected from MQTT server with code: %s" % rc)
    while rc != 0:
        sleep(RECONNECT_DELAY_SECS)
        rc = client.reconnect()


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("config")
    args = p.parse_args()

    with open(args.config) as f:
        config = yaml.load(f)

    client = mqtt.Client()
    user = config["mqtt"].get("user")
    password = config["mqtt"].get("password")
    topic_prefix = config["mqtt"]["topic_prefix"].strip("/")

    if user and password:
        client.username_pw_set(user, password)

    def on_conn(client, userdata, flags, rc):
        for output_config in config["digital_outputs"]:
            topic = "%s/output/%s" % (topic_prefix, output_config["name"])
            client.subscribe(topic, qos=1)
            _LOG.info("Subscribed to topic: %r", topic)

    def on_msg(client, userdata, msg):
        _LOG.info("Got message on topic %r: %r", msg.topic, msg.payload)
        output_name = msg.topic[len("%s/output/" % topic_prefix):]
        output_config = None
        for output in config["digital_outputs"]:
            if output["name"] == output_name:
                output_config = output
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
        gpio.output(output_config["pin"], value)
        _LOG.info("Set output %r to %r", output_config["name"], value)

    client.on_disconnect = on_disconnect
    client.on_connect = on_conn
    client.on_message = on_msg

    gpio.setmode(gpio.BCM)
    last_states = {}

    for input_config in config["digital_inputs"]:
        pud = None
        if input_config["pullup"]:
            pud = gpio.PUD_UP
        elif input_config["pulldown"]:
            pud = gpio.PUD_DOWN
        gpio.setup(input_config["pin"], gpio.IN, pull_up_down=pud)
        last_states[input_config["pin"]] = None

    for output_config in config["digital_outputs"]:
        gpio.setup(output_config["pin"], gpio.OUT)

    client.connect(config["mqtt"]["host"], config["mqtt"]["port"], 60)
    client.loop_start()

    try:
        while True:
            for input_config in config["digital_inputs"]:
                state = bool(gpio.input(input_config["pin"]))
                sleep(0.05)
                if bool(gpio.input(input_config["pin"])) != state:
                    continue
                if state != last_states[input_config["pin"]]:
                    _LOG.info(
                        "Input %r state changed to %r",
                        input_config["name"],
                        state)
                    client.publish(
                        "%s/input/%s" % (topic_prefix, input_config["name"]),
                        payload=(input_config["on_payload"] if state
                                 else input_config["off_payload"]))
                    last_states[input_config["pin"]] = state
            sleep(0.05)
    except KeyboardInterrupt:
        print ""
    finally:
        client.loop_stop()
