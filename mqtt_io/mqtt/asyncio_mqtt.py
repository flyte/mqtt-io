"""
Implementation of AbstractMQTTClient using asyncio-mqtt client.
"""

import asyncio
import logging
from asyncio.queues import QueueFull
from functools import wraps
from typing import Any, Callable, List, Optional, Tuple, TypeVar, cast

from asyncio_mqtt.client import Client, MqttError, Will  # type: ignore
from paho.mqtt import client as paho  # type: ignore

from . import (
    AbstractMQTTClient,
    MQTTClientOptions,
    MQTTException,
    MQTTMessage,
    MQTTMessageSend,
    MQTTProtocol,
)

_LOG = logging.getLogger(__name__)

Func = TypeVar("Func", bound=Callable[..., Any])


def _map_exception(func: Func) -> Func:
    @wraps(func)
    async def inner(*args: Any, **kwargs: Any) -> Any:
        try:
            await func(*args, **kwargs)
        except MqttError as exc:
            raise MQTTException from exc

    return cast(Func, inner)


class MQTTClient(AbstractMQTTClient):
    """
    MQTTClient implementation using asyncio-mqtt client.
    """

    def __init__(self, options: MQTTClientOptions):
        super().__init__(options)
        protocol_map = {
            MQTTProtocol.V31: paho.MQTTv31,
            MQTTProtocol.V311: paho.MQTTv311,
            MQTTProtocol.V5: paho.MQTTv5,
        }
        will = None
        if options.will is not None:
            will = Will(
                topic=options.will.topic,
                payload=options.will.payload,
                qos=options.will.qos,
                retain=options.will.retain,
            )
        tls_context = None
        if options.tls_options is not None:
            tls_context = options.tls_options.ssl_context

        self._client = Client(
            hostname=options.hostname,
            port=options.port,
            username=options.username,
            password=options.password,
            client_id=options.client_id,
            # keepalive=options.keepalive,  # This isn't implemented yet on 0.8.1
            tls_context=tls_context,
            protocol=protocol_map[options.protocol],
            will=will,
            clean_session=options.clean_session,
        )
        self._message_queue: Optional[asyncio.Queue[MQTTMessage]] = None

    @_map_exception
    async def connect(self, timeout: int = 10) -> None:
        await self._client.connect(timeout=timeout)

    @_map_exception
    async def disconnect(self) -> None:
        try:
            await self._client.disconnect()
        except TimeoutError:
            await self._client.force_disconnect()

    @_map_exception
    async def subscribe(self, topics: List[Tuple[str, int]]) -> None:
        await self._client.subscribe(topics)

    @_map_exception
    async def publish(self, msg: MQTTMessageSend) -> None:
        await self._client.publish(
            topic=msg.topic, payload=msg.payload, qos=msg.qos, retain=msg.retain
        )

    def _on_message(
        self, client: paho.Client, userdata: Any, msg: paho.MQTTMessage
    ) -> None:
        if self._message_queue is None:
            _LOG.warning("Discarding MQTT message because queue is not initialised")
            return
        our_msg = MQTTMessage(topic=msg.topic, payload=msg.payload)
        try:
            self._message_queue.put_nowait(our_msg)
        except QueueFull:
            _LOG.warning("Discarding old MQTT message because queue is full")
            self._message_queue.get_nowait()
            self._message_queue.put_nowait(our_msg)

    @property
    def message_queue(self) -> "asyncio.Queue[MQTTMessage]":
        if self._message_queue is None:
            self._message_queue = asyncio.Queue(self._options.message_queue_size)
            # pylint: disable=protected-access
            self._client._client.on_message = (  # type: ignore[attr-defined]
                self._on_message
            )
        return self._message_queue
