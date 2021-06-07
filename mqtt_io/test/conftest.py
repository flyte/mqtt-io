from typing import AsyncIterator, Optional, TypeVar, cast

import pytest
import trio
import yaml
from async_generator import asynccontextmanager

from mqtt_io.events import Event
from mqtt_io.server import MQTTIO

from ..types import ConfigType

EventT = TypeVar("EventT")


# pylint: disable=protected-access


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


async def pin_reads_value(
    mqttio: MQTTIO, pin_name: str, value: bool, last_value: Optional[bool] = None
) -> None:
    in_conf = mqttio.gpio.digital_input_configs[pin_name]
    await mqttio.gpio._handle_digital_input_value(in_conf, value, last_value)
