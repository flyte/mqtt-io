"""
Provides "StreamIo" which handles writing and reading streams.
"""
import logging
from typing import TYPE_CHECKING, Dict, Tuple

import trio

from .abc import GenericIO
from .constants import SEND_SUFFIX, STREAM_TOPIC
from .events import StreamDataReadEvent, StreamDataSentEvent
from .helpers import _init_module, output_name_from_topic
from .modules.stream import GenericStream
from .types import ConfigType, TaskStatus

if TYPE_CHECKING:
    # pylint: disable=cyclic-import
    from .server_trio import MQTTIO

_LOG = logging.getLogger(__name__)


# pylint: enable=duplicate-code
# pylint: disable=too-many-lines


class StreamIO(GenericIO):
    """
    Handles reading and writing to streams.
    """

    def __init__(
        self,
        config: ConfigType,
        server: "MQTTIO",
    ) -> None:
        """
        Initialise Stream modules.
        """
        self.server = server
        # Stream
        self.stream_configs: Dict[str, ConfigType] = {}
        self.stream_modules: Dict[str, GenericStream] = {}
        self.stream_output_channels: Dict[
            str, Tuple[trio.MemorySendChannel, trio.MemoryReceiveChannel]
        ] = {}

        self.config = config

    def _publish_data(
        self, name: str, data: bytes, qos: int = 1, retain: bool = False
    ) -> None:
        self.server.mqtt.publish(
            "/".join((self.server.config["mqtt"]["topic_prefix"], STREAM_TOPIC, name)),
            data,
            qos=qos,
            retain=retain,
        )

    async def init(self) -> None:
        """
        Initialize the modules and starts task for polling.
        """
        # TODO: Tasks pending completion -@flyte at 01/03/2021, 14:40:10
        # Only publish if read: true and only subscribe if write: true

        async def publish_stream_data(
            event_rx: trio.MemoryReceiveChannel,
            task_status: TaskStatus = trio.TASK_STATUS_IGNORED,
        ) -> None:
            event: StreamDataReadEvent
            async with event_rx:
                task_status.started()
                async for event in event_rx:
                    stream_conf = self.stream_configs[event.stream_name]
                    self._publish_data(
                        event.stream_name, event.data, retain=stream_conf["retain"]
                    )

        event_rx = await self.server.event_bus.subscribe(StreamDataReadEvent)
        await self.server.nursery.start(publish_stream_data, event_rx)

        self.stream_configs = {x["name"]: x for x in self.config["stream_modules"]}
        self.stream_modules = {}
        for stream_conf in self.config["stream_modules"]:
            stream_module = await _init_module(
                stream_conf, "stream", self.config["options"]["install_requirements"]
            )
            self.stream_modules[stream_conf["name"]] = stream_module

            self.server.nursery.start_soon(self.stream_poller, stream_module, stream_conf)

            # Set up a stream output channel.
            tx_chan, rx_chan = trio.open_memory_channel(0)
            self.stream_output_channels[stream_conf["name"]] = (tx_chan, rx_chan)

            # Queue a stream output loop task
            self.server.nursery.start_soon(
                self.stream_output_loop, stream_module, stream_conf, rx_chan
            )

            # await trio.sleep(1)
            await self.server.mqtt.subscribe(
                "/".join(
                    (
                        self.config["mqtt"]["topic_prefix"],
                        STREAM_TOPIC,
                        stream_conf["name"],
                        SEND_SUFFIX,
                    )
                )
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
                    self.server.event_bus.fire(
                        StreamDataReadEvent(stream_conf["name"], data)
                    )
            await trio.sleep(stream_conf["read_interval"])

    async def stream_output_loop(
        self,
        module: GenericStream,
        stream_conf: ConfigType,
        data_rx: trio.MemoryReceiveChannel,
    ) -> None:
        """
        Wait for data to appear on the queue, then send it to the stream.
        """
        data: bytes
        async for data in data_rx:
            try:
                await module.async_write(data)
            except Exception:  # pylint: disable=broad-except
                _LOG.exception(
                    "Exception while sending data to stream '%s':", stream_conf["name"]
                )
            else:
                self.server.event_bus.fire(StreamDataSentEvent(stream_conf["name"], data))

    async def handle_mqtt_msg(self, topic: str, payload: bytes) -> None:
        # Handle stream send message
        if topic.endswith("/send"):
            await self.handle_stream_send_msg(topic, payload)

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
            tx_chan, _ = self.stream_output_channels[stream_name]
        except KeyError:
            _LOG.warning("No stream output queue found named %r", stream_name)
        try:
            tx_chan.send_nowait(payload)
        except trio.WouldBlock:
            _LOG.error(
                "'%s' stream output channel full when handling stream send message",
                stream_name,
            )

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
