"""
Provides "StreamIo" which handles writing and reading streams.
"""
import asyncio
import logging
from functools import partial
from typing import Dict, List, TYPE_CHECKING

from .constants import (
    MQTT_SUB_PRIORITY,
    SEND_SUFFIX,
    STREAM_TOPIC,
)
from .events import (
    StreamDataReadEvent,
    StreamDataSentEvent,
)
from .helpers import output_name_from_topic, _init_module
from .modules.stream import GenericStream
from .types import ConfigType
from .utils import PriorityCoro
if TYPE_CHECKING:
    # pylint: disable=cyclic-import
    from .server import MqttIo
_LOG = logging.getLogger(__name__)


# pylint: enable=duplicate-code
# pylint: disable=too-many-lines

class StreamIo:
    """
    Handles reading and writing to streams.
    """
    def __init__(self, config: ConfigType, server: "MqttIo", ) -> None:
        """
        Initialise Stream modules.
        """
        self.server = server
        # Stream
        self.stream_configs: Dict[str, ConfigType] = {}
        self.stream_modules: Dict[str, GenericStream] = {}
        self.stream_output_queues = {}  # type: Dict[str, asyncio.Queue[bytes]]

        self.config = config

    def init(self) -> None:
        """
        Initialize the modules and starts task for polling.
        """
        server = self.server

        # TODO: Tasks pending completion -@flyte at 01/03/2021, 14:40:10
        # Only publish if read: true and only subscribe if write: true

        async def publish_stream_data_callback(event: StreamDataReadEvent) -> None:
            stream_conf = self.stream_configs[event.stream_name]
            server.new_publish_task(
                stream_conf["name"], stream_conf["retain"], event.data, STREAM_TOPIC
            )

        server.event_bus.subscribe(StreamDataReadEvent, publish_stream_data_callback)

        self.stream_configs = {x["name"]: x for x in self.config["stream_modules"]}
        self.stream_modules = {}
        sub_topics: List[str] = []
        for stream_conf in self.config["stream_modules"]:
            stream_module = _init_module(
                stream_conf, "stream", self.config["options"]["install_requirements"]
            )
            self.stream_modules[stream_conf["name"]] = stream_module

            server.transient_task_queue.add_task(
                server.loop.create_task(self.stream_poller(stream_module, stream_conf))
            )

            # Set up a stream output queue.
            queue = asyncio.Queue()  # type: asyncio.Queue[bytes]
            self.stream_output_queues[stream_conf["name"]] = queue

            # Queue a stream output loop task
            server.transient_task_queue.add_task(
                server.loop.create_task(
                    # Use partial to avoid late binding closure
                    partial(
                        self.stream_output_loop,
                        stream_module,
                        stream_conf,
                        self.stream_output_queues[stream_conf["name"]],
                    )()
                )
            )

            sub_topics.append(
                "/".join(
                    (
                        self.config["mqtt"]["topic_prefix"],
                        STREAM_TOPIC,
                        stream_conf["name"],
                        SEND_SUFFIX,
                    )
                )
            )

        # Subscribe to stream send topics
        if sub_topics:
            server.mqtt_task_queue.put_nowait(
                PriorityCoro(server.mqtt_subscribe(sub_topics), MQTT_SUB_PRIORITY)
            )

    async def stream_poller(self, module: GenericStream, stream_conf: ConfigType) -> None:
        """
        Poll a stream at a given interval and fire the StreamDataReadEvent with read data.
        """
        while True:
            try:
                data = await module.async_read()
            except Exception:  # pylint: disable=broad-except
                _LOG.exception(
                    "Exception while polling stream '%s':", stream_conf["name"]
                )
            else:
                if data is not None:
                    self.server.event_bus.fire(StreamDataReadEvent(stream_conf["name"], data))
            await asyncio.sleep(stream_conf["read_interval"])

    async def stream_output_loop(
            self,
            module: GenericStream,
            stream_conf: ConfigType,
            queue: "asyncio.Queue[bytes]",
    ) -> None:
        """
        Wait for data to appear on the queue, then send it to the stream.
        """
        while True:
            data = await queue.get()
            try:
                await module.async_write(data)
            except Exception:  # pylint: disable=broad-except
                _LOG.exception(
                    "Exception while sending data to stream '%s':", stream_conf["name"]
                )
            else:
                self.server.event_bus.fire(StreamDataSentEvent(stream_conf["name"], data))

    async def handle_stream_send_msg(self, topic: str, payload: bytes) -> None:
        """
        Handles writing of messages to the stream.
        """
        try:
            stream_name = output_name_from_topic(
                topic, self.config["mqtt"]["topic_prefix"], STREAM_TOPIC
            )
        except ValueError as exc:
            _LOG.warning("Unable to parse stream name from topic: %s", exc)
            return
        try:
            self.stream_output_queues[stream_name].put_nowait(payload)
        except KeyError:
            _LOG.warning("No stream output queue found named %r", stream_name)

    def cleanup(self) -> None:
        """
        Cleans up all modules
        """
        for module in self.stream_modules.values():
            _LOG.debug("Running cleanup on module %s", module)
            try:
                module.cleanup()
            except Exception:  # pylint: disable=broad-except
                _LOG.exception(
                    "Exception while cleaning up stream module %s",
                    module,
                )
