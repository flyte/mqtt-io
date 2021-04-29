"""
Provides "SensorIo" which handles reading of sensor values
"""
import asyncio
import logging
from typing import Dict, TYPE_CHECKING

import backoff  # type: ignore

from .config import (
    validate_and_normalise_sensor_input_config,
)
from .constants import (
    SENSOR_TOPIC,
)
from .events import (
    SensorReadEvent,
)
from .helpers import _init_module
from .modules.sensor import GenericSensor
from .types import ConfigType, SensorValueType

if TYPE_CHECKING:
    # pylint: disable=cyclic-import
    from .server import MqttIo
_LOG = logging.getLogger(__name__)


# pylint: enable=duplicate-code
# pylint: disable=too-many-lines

# pylint: disable=too-few-public-methods

class SensorIo:
    """
    Handles the modules for reading sensor values.
    Normally part of an instance of MqttIo
    """

    def __init__(self, config: ConfigType, server: "MqttIo") -> None:
        self.config = config
        self.server = server
        # Sensor
        self.sensor_configs: Dict[str, ConfigType] = {}
        self.sensor_input_configs: Dict[str, ConfigType] = {}
        self.sensor_modules: Dict[str, GenericSensor] = {}

    def init(self) -> None:
        """
        Initializes the modules and inputs.
        """
        self._init_sensor_modules()
        self._init_sensor_inputs()

    def _init_sensor_modules(self) -> None:
        """
        Initialise Sensor modules.
        """
        self.sensor_configs = {x["name"]: x for x in self.config["sensor_modules"]}
        self.sensor_modules = {}
        for sens_config in self.config["sensor_modules"]:
            self.sensor_modules[sens_config["name"]] = _init_module(
                sens_config, "sensor", self.config["options"]["install_requirements"]
            )

    def _init_sensor_inputs(self) -> None:
        async def publish_sensor_callback(event: SensorReadEvent) -> None:
            sens_conf = self.sensor_input_configs[event.sensor_name]
            digits: int = sens_conf["digits"]
            self.server.new_publish_task(
                event.sensor_name, sens_conf["retain"],
                f"{event.value:.{digits}f}".encode("utf8"),
                SENSOR_TOPIC
            )

        self.server.event_bus.subscribe(SensorReadEvent, publish_sensor_callback)

        for sens_conf in self.config["sensor_inputs"]:
            sensor_module = self.sensor_modules[sens_conf["module"]]
            sens_conf = validate_and_normalise_sensor_input_config(
                sens_conf, sensor_module
            )
            self.sensor_input_configs[sens_conf["name"]] = sens_conf

            sensor_module.setup_sensor(sens_conf)

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
                        self.server.event_bus.fire(SensorReadEvent(sens_conf["name"], value))
                    await asyncio.sleep(sens_conf["interval"])

            self.server.transient_task_queue.add_task(self.server.loop.create_task(poll_sensor()))

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
