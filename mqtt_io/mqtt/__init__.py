"""
Abstraction layer for MQTT clients to enable easier switching out.
"""
import abc
import asyncio
import ssl
from dataclasses import dataclass
from enum import Enum, auto
from importlib import import_module
from typing import List, Optional, Tuple, Type


class MQTTProtocol(Enum):
    """
    MQTT protocol.
    """

    V31 = auto()
    V311 = auto()
    V5 = auto()


@dataclass
class MQTTMessage:
    """
    MQTT message.
    """

    topic: str
    payload: Optional[bytes] = None


@dataclass
class MQTTMessageSend(MQTTMessage):
    """
    MQTT message being sent.
    """

    qos: int = 0
    retain: bool = False


@dataclass
class MQTTWill:
    """
    MQTT will.
    """

    topic: str
    payload: Optional[bytes]
    qos: int
    retain: bool


@dataclass
class MQTTTLSOptions:
    """
    MQTT TLS options.
    """

    ca_certs: Optional[str] = None
    certfile: Optional[str] = None
    keyfile: Optional[str] = None
    cert_reqs: int = ssl.CERT_REQUIRED
    tls_version: int = ssl.PROTOCOL_TLS
    ciphers: Optional[str] = None

    @property
    def ssl_context(self) -> ssl.SSLContext:
        """
        The TLS options as an ssl.SSLContext object.
        """
        context = ssl.SSLContext(self.tls_version)

        if self.certfile is not None:
            context.load_cert_chain(self.certfile, self.keyfile)

        if self.cert_reqs == ssl.CERT_NONE:
            context.check_hostname = False

        context.verify_mode = self.cert_reqs or ssl.CERT_REQUIRED

        if self.ca_certs is None:
            context.load_default_certs()
        else:
            context.load_verify_locations(self.ca_certs)

        if self.ciphers is not None:
            context.set_ciphers(self.ciphers)

        return context


@dataclass
class MQTTClientOptions:  # pylint: disable=too-many-instance-attributes
    """
    MQTT client options.
    """

    hostname: str
    client_id: str
    port: int = 1883
    username: Optional[str] = None
    password: Optional[str] = None
    tls_options: Optional[MQTTTLSOptions] = None
    protocol: MQTTProtocol = MQTTProtocol.V311
    clean_session: Optional[bool] = None
    keepalive: int = 60
    will: Optional[MQTTWill] = None
    message_queue_size: int = 1000


class AbstractMQTTClient(abc.ABC):
    """
    Abstract MQTT client interface to enable easier switching out of MQTT client
    implementations.
    """

    @abc.abstractmethod
    def __init__(self, options: MQTTClientOptions):
        """
        Initialisation.
        """
        self._options = options

    @abc.abstractmethod
    async def connect(self, timeout: int = 10) -> None:
        """
        Connect to MQTT server.
        """

    @abc.abstractmethod
    async def disconnect(self) -> None:
        """
        Disconnect from MQTT server.
        """

    @abc.abstractmethod
    async def subscribe(self, topics: List[Tuple[str, int]]) -> None:
        """
        Subscribe to a list of topics.
        """

    @abc.abstractmethod
    async def publish(self, msg: MQTTMessageSend) -> None:
        """
        Publish an MQTT message.
        """

    @property
    @abc.abstractmethod
    def message_queue(self) -> "asyncio.Queue[MQTTMessage]":
        """
        Get the queue onto which received MQTT messages are put.
        """

    @staticmethod
    def get_implementation(module_name: str) -> Type["AbstractMQTTClient"]:
        """
        Import an implemenation of AbstractMQTTClient and return its class.
        """
        client_module = import_module(module_name)
        client: Type["AbstractMQTTClient"]
        client = client_module.MQTTClient  # type: ignore[attr-defined]
        return client


class MQTTException(Exception):
    """
    An Exception which should be raised on errors in implementations of AbstractMQTTClient
    """
