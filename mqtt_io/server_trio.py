import logging
from typing import Any, Dict, Optional

import trio
from paho.mqtt import client as paho
from trio_paho_mqtt import AsyncClient

_LOG = logging.getLogger(__name__)


class MQTTIO:
    def __init__(self, config: Dict[str, Any]):
        self._main_nursery: Optional[trio.Nursery] = None
        self._mqtt_nursery: Optional[trio.Nursery] = None

    async def run_mqtt(self):
        async def handle_messages(client: AsyncClient) -> None:
            async for msg in client.messages():
                print(msg)

        while True:
            try:
                async with trio.open_nursery() as nursery:
                    self._mqtt_nursery = nursery
                    client = AsyncClient(paho.Client(), nursery)
                    client.connect("test.mosquitto.org", 1883)

                    await handle_messages(client)

                    nursery.cancel_scope.cancel()
            except Exception:  # pylint: disable=broad-except
                _LOG.exception("Exception in Mqtt.Connect():")
            finally:
                await trio.sleep(1)

    async def run_async(self):
        async with trio.open_nursery() as nursery:
            self._main_nursery = nursery
            nursery.start_soon(self.run_mqtt)

    def run(self):
        # signals stuff

        # gpio, sensor, stream init

        trio.run(self.run_async)
