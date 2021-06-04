from typing import AsyncContextManager, AsyncGenerator, AsyncIterator, cast

import pytest
import trio
import yaml
from async_generator import asynccontextmanager

from mqtt_io.server import MQTTIO

from ..types import ConfigType


class ConfigBuilder:
    def __init__(self) -> None:
        self._raw_config: ConfigType = {}

    def add_list_section_entry(self, section_title: str, data_yaml: str) -> None:
        """
        Add given yaml data to a toplevel list section. Adds the section if not exists.
        """
        data = yaml.safe_load(data_yaml)
        self._raw_config.setdefault(section_title, []).append(data)

    def add_dict_section_data(self, section_title: str, data_yaml: str) -> None:
        """
        Add given yaml data to a toplevel dict section. Adds the section if not exists.
        """
        data = yaml.safe_load(data_yaml)
        self._raw_config.setdefault(section_title, {}).update(data)

    def add_toplevel_section(self, section_title: str, data_yaml: str) -> None:
        """
        Add toplevel section containing the given yaml data.
        """
        data = yaml.safe_load(data_yaml)
        self._raw_config[section_title] = data

    def add_minimal_config(self) -> None:
        """
        Add the minimal necessities for a valid config.
        """
        self._raw_config["mqtt"] = dict(host="localhost")

    def clear(self) -> None:
        """
        Clear the config.
        """
        self._raw_config = {}

    @property
    def config(self) -> ConfigType:
        return self._raw_config

    @property
    def yaml(self) -> str:
        return cast(str, yaml.dump(self._raw_config))


@pytest.fixture
def config_builder() -> ConfigBuilder:
    return ConfigBuilder()


# @asynccontextmanager
# async def running_mqttio(mqttio: MQTTIO) -> AsyncIterator[None]:
#     async with trio.open_nursery() as nursery:
#         mqttio._main_nursery = nursery
#         await nursery.start(mqttio.event_bus.run)
#         yield
