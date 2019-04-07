import logging

from hbmqtt.client import MQTTClient, ClientException
from hbmqtt.mqtt.constants import QOS_1, QOS_2


async def connect(host, **kwargs):
    client = MQTTClient()
    await client.connect("mqtt://%s" % host, **kwargs)
    return client


async def subscribe(client, topics, **kwargs):
    return await client.subscribe(topics, **kwargs)

