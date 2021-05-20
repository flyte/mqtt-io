"""
Helpers
"""
import logging
import re
from importlib import import_module
from typing import Any, Dict, Type, Union, overload

from typing_extensions import Literal

from .config import (
    get_main_schema_section,
    validate_and_normalise_config,
)
from .constants import (
    MODULE_CLASS_NAMES,
    MODULE_IMPORT_PATH,
)
from .modules import install_missing_module_requirements
from .modules.gpio import GenericGPIO
from .modules.sensor import GenericSensor
from .modules.stream import GenericStream

_LOG = logging.getLogger(__name__)


@overload
async def _init_module(
    module_config: Dict[str, Dict[str, Any]],
    module_type: Literal["gpio"],
    install_requirements: bool,
) -> GenericGPIO:
    ...  # pragma: no cover


@overload
async def _init_module(
    module_config: Dict[str, Dict[str, Any]],
    module_type: Literal["sensor"],
    install_requirements: bool,
) -> GenericSensor:
    ...  # pragma: no cover


@overload
async def _init_module(
    module_config: Dict[str, Dict[str, Any]],
    module_type: Literal["stream"],
    install_requirements: bool,
) -> GenericStream:
    ...  # pragma: no cover


async def _init_module(
    module_config: Dict[str, Dict[str, Any]], module_type: str, install_requirements: bool
) -> Union[GenericGPIO, GenericSensor, GenericStream]:
    """
    Initialise a GPIO module by:
    - Importing it
    - Validating its config
    - Installing any missing requirements for it
    - Instantiating its class
    """
    module = import_module(
        "%s.%s.%s" % (MODULE_IMPORT_PATH, module_type, module_config["module"])
    )
    # Doesn't need to be a deep copy because we're not mutating the base rules
    module_schema = get_main_schema_section(f"{module_type}_modules")
    # Add the module's config schema to the base schema
    module_schema.update(getattr(module, "CONFIG_SCHEMA", {}))
    module_config = validate_and_normalise_config(module_config, module_schema)
    if install_requirements:
        await install_missing_module_requirements(module)
    module_class: Type[Union[GenericGPIO, GenericSensor, GenericStream]] = getattr(
        module, MODULE_CLASS_NAMES[module_type]
    )
    return module_class(module_config)


def output_name_from_topic(topic: str, prefix: str, topic_type: str) -> str:
    """
    Parses an MQTT topic and returns the name of the output that the message relates to.
    """
    match = re.match(f"^{prefix}/{topic_type}/(.+?)/.+$", topic)
    if match is None:
        raise ValueError("Topic %r does not adhere to expected structure" % topic)
    return match.group(1)
