import pytest
import time
import argparse

import paho.mqtt.client as mqtt
from pi_mqtt_gpio import server

pytestmark = pytest.mark.mqtt


receive = []

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe("$SYS/#")

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    print(msg.topic+" "+str(msg.payload))

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

@pytest.fixture(autouse=True)
def test_raspberrypi_setup_teardown():
    # reset the digital_inputs, digital_outputs before each test
    client.reinitialise()
    client.connect("localhost", 1883, 60)
    time.sleep(0.5) # wait for receivs and delete them.
    del receive[:]

    # A test function will be run at this point
    yield

    # Code that will run after your test, for example:

def test_connect():
    # setup outputs and inputs for interrupt tests for rising edges
    args = argparse.Namespace()
    args.config = "config.example.yml"
    server.main(args)
#client.loop_forever()
