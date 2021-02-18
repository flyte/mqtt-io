"""
Handles config validation and normalisation.
"""

from __future__ import annotations

import logging
from collections import Counter
from os.path import dirname, join, realpath
from typing import (
    IO,
    TYPE_CHECKING,
    Any,
    Dict,
    Iterable,
    List,
    Optional,
    Set,
    TextIO,
    Union,
)

import cerberus  # type: ignore
import yaml

from .exceptions import ConfigValidationFailed
from .types import ConfigType

if TYPE_CHECKING:
    from .modules.gpio import GenericGPIO
    from .modules.sensor import GenericSensor

_LOG = logging.getLogger(__name__)


class ConfigValidator(cerberus.Validator):  # type: ignore # No stubs for Cerberus
    """
    Cerberus Validator containing function(s) for use with validating or
    coercing values relevant to the MQTT IO project.
    """

    @staticmethod
    def _normalize_coerce_rstrip_slash(value: str) -> str:
        """
        Strip forward slashes from the end of the string.
        :param value: String to strip forward slashes from
        :type value: str
        :return: String without forward slashes on the end
        :rtype: str
        """
        return value.rstrip("/")

    @staticmethod
    def _normalize_coerce_tostring(value: Any) -> str:
        """
        Convert value to string.
        :param value: Value to convert
        :return: Value represented as a string.
        :rtype: str
        """
        return str(value)


def get_duplicate_names(io_conf: List[ConfigType]) -> List[str]:
    """
    Checks for any duplicated names in a list of dicts, such as the gpio_modules section
    of the config.
    """
    counter = Counter(x["name"] for x in io_conf)
    return [name for name, count in counter.items() if count > 1]


def validate_gpio_module_names(
    bad_configs: Dict[str, Dict[str, List[str]]],
    config: ConfigType,
    module_section: str,
    io_sections: Iterable[str],
) -> None:
    """
    Ensure that all of the IO config sections refer to existing module names.
    """
    module_names = {x["name"] for x in config.get(module_section, [])}

    for io_section in io_sections:
        for io_conf in config.get(io_section, []):
            if io_conf["module"] not in module_names:
                bad_configs.setdefault(io_section, {}).setdefault(
                    io_conf["name"], []
                ).append(
                    "%s section has no module configured with the name '%s'"
                    % (
                        module_section,
                        io_conf["module"],
                    )
                )


def validate_gpio_interrupt_for(
    bad_configs: Dict[str, Dict[str, List[str]]],
    digital_inputs: List[ConfigType],
) -> None:
    """
    Ensure that all of the pins listed in interrupt_for are configured as interrupts.
    """
    interrupt_pins: Set[str] = set(
        in_conf["name"] for in_conf in digital_inputs if in_conf.get("interrupt")
    )
    for in_conf in [x for x in digital_inputs if x.get("interrupt_for")]:
        for pin_name in in_conf["interrupt_for"]:
            errors = []
            if pin_name not in interrupt_pins:
                errors.append(
                    f"Pin '{pin_name}' listed in 'interrupt_for' is not configured as an "
                    "interrupt itself"
                )
            if pin_name == in_conf["name"]:
                errors.append(f"Pin '{pin_name}' lists itself in 'interrupt_for'")
            if errors:
                all_errors = bad_configs.setdefault("digital_inputs", {}).setdefault(
                    in_conf["name"], []
                )
                all_errors += errors


def get_main_schema() -> Any:
    """
    Load the main config schema from the yaml file packaged in the same dir as this file.
    :return: Config schema
    :rtype: dict
    """
    schema_path = join(dirname(realpath(__file__)), "config.schema.yml")
    return yaml.safe_load(open(schema_path))


def validate_and_normalise_config(
    config: Any, schema: Any, **validator_options: Any
) -> ConfigType:
    """
    Validate the config dict based on the config schema.
    :param config: The supplied configuration
    :type config: dict
    :param schema: The schema against which to validate the config
    :type schema: dict
    :return: Normalised config
    :rtype: dict
    """
    validator = ConfigValidator(schema, **validator_options)
    if not validator.validate(config):
        raise ConfigValidationFailed(
            "Config did not validate:\n%s" % yaml.dump(validator.errors)
        )
    validated_config: ConfigType = validator.normalized(config)
    return validated_config


def custom_validate_main_config(config: ConfigType) -> ConfigType:
    """
    Do our own validation on the config to make sure it contains sane, workable data.
    """
    unique_name_sections = (
        "gpio_modules",
        "sensor_modules",
        "stream_modules",
        "digital_inputs",
        "digital_outputs",
        "sensor_inputs",
        "stream_reads",
        "stream_writes",
    )

    # Make sure none of the lists use a name multiple times
    sections_with_duplicated_names = {}
    for config_section in unique_name_sections:
        duplicate_names = get_duplicate_names(config.get(config_section, []))
        if duplicate_names:
            sections_with_duplicated_names[config_section] = duplicate_names

    if sections_with_duplicated_names:
        raise ConfigValidationFailed(
            "Config did not validate due to duplicated names:\n%s"
            % yaml.dump(sections_with_duplicated_names)
        )

    bad_configs: Dict[str, Dict[str, List[str]]] = {}

    # Make sure each of the IO configs refer to an existing module config
    module_and_io_sections = dict(
        gpio_modules=("digital_inputs", "digital_outputs"),
        sensor_modules=("sensor_inputs",),
        stream_modules=("stream_reads", "stream_writes"),
    )
    for module_section, io_sections in module_and_io_sections.items():
        validate_gpio_module_names(bad_configs, config, module_section, io_sections)

    # Make sure all digital inputs listed in 'interrupt_for' lists are configured
    # as interrupts themselves.
    validate_gpio_interrupt_for(bad_configs, config["digital_inputs"])

    if bad_configs:
        raise ConfigValidationFailed(
            "Config did not validate due to errors in the following sections:\n%s"
            % yaml.dump(bad_configs)
        )
    return config


def load_main_config(path: str) -> ConfigType:
    """
    Read the main config file from the given path, validate it and return it normalised.
    :param path: The filesystem path
    :return: The config
    """
    with open(path, "r") as stream:
        raw_config = yaml.safe_load(stream)
    return validate_and_normalise_main_config(raw_config)


def validate_and_normalise_main_config(raw_config: Any) -> ConfigType:
    """
    Validate and normalise any raw config object with the main schema.
    """
    config = validate_and_normalise_config(raw_config, get_main_schema())
    config = custom_validate_main_config(config)
    return config


def validate_and_normalise_sensor_input_config(
    config: ConfigType, module: GenericSensor
) -> ConfigType:
    """
    Validate sensor input configs.
    """
    schema = get_main_schema()
    sensor_input_schema = schema["sensor_inputs"]["schema"]["schema"].copy()
    sensor_input_schema.update(getattr(module, "SENSOR_SCHEMA", {}))
    return validate_and_normalise_config(config, sensor_input_schema, allow_unknown=False)


def validate_and_normalise_digital_input_config(
    config: ConfigType, module: GenericGPIO
) -> ConfigType:
    """
    Validate digital input configs.
    """
    schema = get_main_schema()
    digital_input_schema = schema["digital_inputs"]["schema"]["schema"].copy()
    digital_input_schema.update(getattr(module, "PIN_SCHEMA", {}))
    digital_input_schema.update(getattr(module, "INPUT_SCHEMA", {}))
    return validate_and_normalise_config(
        config, digital_input_schema, allow_unknown=False
    )


def validate_and_normalise_digital_output_config(
    config: ConfigType, module: GenericGPIO
) -> ConfigType:
    """
    Validate digital output configs.
    """
    schema = get_main_schema()
    digital_output_schema = schema["digital_outputs"]["schema"]["schema"].copy()
    digital_output_schema.update(getattr(module, "PIN_SCHEMA", {}))
    digital_output_schema.update(getattr(module, "OUTPUT_SCHEMA", {}))
    return validate_and_normalise_config(
        config, digital_output_schema, allow_unknown=False
    )
