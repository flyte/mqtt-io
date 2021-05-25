"""
Provides "SensorIo" which handles reading of sensor values
"""
import logging
from typing import TYPE_CHECKING, Dict

import backoff  # type: ignore
import trio
from trio_typing import TaskStatus

from .abc import GenericIO
from .config import validate_and_normalise_sensor_input_config
from .constants import SENSOR_TOPIC
from .events import SensorReadEvent
from .helpers import _init_module
from .modules.sensor import GenericSensor
from .types import ConfigType, SensorValueType

if TYPE_CHECKING:
    # pylint: disable=cyclic-import
    from .server import MQTTIO
_LOG = logging.getLogger(__name__)


# pylint: enable=duplicate-code
# pylint: disable=too-many-lines

# pylint: disable=too-few-public-methods


class SensorIO(GenericIO):
    """
    Handles the modules for reading sensor values.
    Intended to be a mixin for MQTTIO.
    """

    def __init__(self, config: ConfigType, server: "MQTTIO") -> None:
        self.config = config
        self.server = server
        # Sensor
        self.sensor_configs: Dict[str, ConfigType] = {}
        self.sensor_input_configs: Dict[str, ConfigType] = {}
        self.sensor_modules: Dict[str, GenericSensor] = {}

    async def init(self) -> None:
        """
        Initializes the modules and inputs.
        """
        await self._init_sensor_modules()
        await self._init_sensor_inputs()

    async def _init_sensor_modules(self) -> None:
        """
        Initialise Sensor modules.
        """
        self.sensor_configs = {x["name"]: x for x in self.config["sensor_modules"]}
        self.sensor_modules = {}
        for sens_config in self.config["sensor_modules"]:
            self.sensor_modules[sens_config["name"]] = await _init_module(
                sens_config,
                "sensor",
                self.config["options"]["install_requirements"],
            )

    def _publish_read(
        self, name: str, value: str, qos: int = 1, retain: bool = False
    ) -> None:
        self.server.mqtt.publish(
            "/".join((self.server.config["mqtt"]["topic_prefix"], SENSOR_TOPIC, name)),
            value.encode("utf8"),
            qos=qos,
            retain=retain,
        )

    async def _init_sensor_inputs(self) -> None:
        async def publish_sensor_reads(
            event_rx: trio.MemoryReceiveChannel,
            task_status: TaskStatus[None] = trio.TASK_STATUS_IGNORED,
        ) -> None:
            event: SensorReadEvent
            async with event_rx:
                task_status.started()
                async for event in event_rx:
                    sens_conf = self.sensor_input_configs[event.sensor_name]
                    digits: int = sens_conf["digits"]
                    self._publish_read(
                        event.sensor_name,
                        f"{event.value:.{digits}f}",
                        retain=sens_conf["retain"],
                    )

        event_rx = await self.server.event_bus.subscribe(SensorReadEvent)
        await self.server.nursery.start(publish_sensor_reads, event_rx)

        for sens_conf in self.config["sensor_inputs"]:
            sensor_module = self.sensor_modules[sens_conf["module"]]
            sens_conf = validate_and_normalise_sensor_input_config(
                sens_conf, sensor_module
            )
            self.sensor_input_configs[sens_conf["name"]] = sens_conf

            await trio.to_thread.run_sync(sensor_module.setup_sensor, sens_conf)

            # Use default args to the function to get around the late binding closures
            async def poll_sensor(
                sensor_module: GenericSensor = sensor_module,
                sens_conf: ConfigType = sens_conf,
            ) -> None:
                @backoff.on_exception(  # type: ignore
                    backoff.expo, Exception, max_time=sens_conf["interval"]
                )
                @backoff.on_predicate(  # type: ignore
                    backoff.expo, lambda x: x is None, max_time=sens_conf["interval"]
                )
                async def get_sensor_value(
                    sensor_module: GenericSensor = sensor_module,
                    sens_conf: ConfigType = sens_conf,
                ) -> SensorValueType:
                    return await sensor_module.async_get_value(sens_conf)

                while True:
                    value = None
                    try:
                        value = await get_sensor_value()
                    except Exception:  # pylint: disable=broad-except
                        _LOG.exception(
                            "Exception when retrieving value from sensor %r:",
                            sens_conf["name"],
                        )
                    if value is not None:
                        value = round(value, sens_conf["digits"])
                        _LOG.info(
                            "Read sensor '%s' value of %s", sens_conf["name"], value
                        )
                        self.server.event_bus.fire(
                            SensorReadEvent(sens_conf["name"], value)
                        )
                    await trio.sleep(sens_conf["interval"])

            self.server.nursery.start_soon(poll_sensor)

    def cleanup(self) -> None:
        """
        Cleans up all modules
        """
        for module in self.sensor_modules.values():
            _LOG.debug("Running cleanup on module %s", module)
            try:
                module.cleanup()
            except Exception:  # pylint: disable=broad-except
                _LOG.exception(
                    "Exception while cleaning up sensor module %s",
                    module,
                )
