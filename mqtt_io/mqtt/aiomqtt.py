"""
Implementation of AbstractMQTTClient using asyncio-mqtt client.
"""

import asyncio
import logging
from asyncio.queues import QueueFull
from functools import wraps
from typing import Any, Callable, List, Optional, Tuple, TypeVar, cast

from aiomqtt.client import Client, MqttError, Will, ProtocolVersion  # type: ignore
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
    """
    Creates a decorator that wraps a function and maps any raised `MqttError`
    exception to a `MQTTException`.

    :param func: The function to be wrapped.
    :type func: Func
    :return: The wrapped function.
    :rtype: Func
    """
    @wraps(func)
    async def inner(*args: Any, **kwargs: Any) -> Any:
        """
        Decorator for asynchronous functions that catches `MqttError` exceptions
        and raises `MQTTException` instead.

        Parameters:
            func (Callable): The function to be decorated.

        Returns:
            Callable: The decorated function.
        """
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
        """
        Initializes a new instance of the MQTTClient class.

        Args:
            options (MQTTClientOptions): The options for the MQTT client.

        Returns:
            None
        """
        super().__init__(options)
        protocol_map = {
            MQTTProtocol.V31: ProtocolVersion.V31,
            MQTTProtocol.V311: ProtocolVersion.V311,
            MQTTProtocol.V5: ProtocolVersion.V5,
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
            identifier=options.client_id,
            #keepalive=options.keepalive,
            tls_context=tls_context,
            protocol=protocol_map[options.protocol],
            will=will,
            clean_session=options.clean_session,
        )
        self._message_queue: Optional[asyncio.Queue[MQTTMessage]] = None

    @_map_exception
    async def connect(self, timeout: int = 10) -> None:
        """
        Connects to the client asynchronously.

        Args:
            timeout (int): The timeout value in seconds (default: 10).

        Returns:
            None: This function does not return anything.
        """
        await self._client.__aenter__() # pylint: disable=unnecessary-dunder-call

    @_map_exception
    async def disconnect(self) -> None:
        """
        This function is an asynchronous method that handles the disconnection of the client.

        Parameters:
            self: The current instance of the class.

        Returns:
            None
        """
        await self._client.__aexit__(None, None, None)

    @_map_exception
    async def subscribe(self, topics: List[Tuple[str, int]]) -> None:
        """
        Subscribe to the given list of topics.

        Args:
            topics (List[Tuple[str, int]]): A list of tuples representing the topics
                to subscribe to.
            Each tuple should contain a string representing the topic name and
                an integer representing the QoS level.

        Returns:
            None: This function does not return anything.

        Raises:
            Exception: If there is an error while subscribing to the topics.

        """
        await self._client.subscribe(topics)

    @_map_exception
    async def publish(self, msg: MQTTMessageSend) -> None:
        """
        Publishes an MQTT message to the specified topic.

        Args:
            msg (MQTTMessageSend): The MQTT message to be published.

        Returns:
            None: This function does not return anything.
        """
        await self._client.publish(
            topic=msg.topic, payload=msg.payload, qos=msg.qos, retain=msg.retain
        )

    def _on_message(
        self, client: paho.Client, userdata: Any, msg: paho.MQTTMessage
    ) -> None:
        """
        Callback function that is called when a message is received through MQTT.

        Args:
            client (paho.Client): The MQTT client instance.
            userdata (Any): The user data associated with the client.
            msg (paho.MQTTMessage): The received MQTT message.

        Returns:
            None: This function does not return anything.
        """
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
        """
        Returns the message queue for receiving MQTT messages.

        :return: The message queue for receiving MQTT messages.
        :rtype: asyncio.Queue[MQTTMessage]
        """
        if self._message_queue is None:
            self._message_queue = asyncio.Queue(self._options.message_queue_size)
            # pylint: disable=protected-access
            self._client._client.on_message = (  # type: ignore[attr-defined]
                self._on_message
            )
        return self._message_queue
