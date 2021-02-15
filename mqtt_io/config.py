import logging
from collections import Counter
from os.path import dirname, join, realpath
from typing import Any, Dict

import cerberus
import yaml

from .exceptions import ConfigValidationFailed

_LOG = logging.getLogger(__name__)


class ConfigValidator(cerberus.Validator):
    """
    Cerberus Validator containing function(s) for use with validating or
    coercing values relevant to the MQTT IO project.
    """

    @staticmethod
    def _normalize_coerce_rstrip_slash(value):
        """
        Strip forward slashes from the end of the string.
        :param value: String to strip forward slashes from
        :type value: str
        :return: String without forward slashes on the end
        :rtype: str
        """
        return value.rstrip("/")

    @staticmethod
    def _normalize_coerce_tostring(value):
        """
        Convert value to string.
        :param value: Value to convert
        :return: Value represented as a string.
        :rtype: str
        """
        return str(value)


def get_duplicate_names(io_conf: list) -> list:
    """
    Checks for any duplicated names in a list of dicts, such as the gpio_modules section
    of the config.
    """
    counter = Counter(x["name"] for x in io_conf)
    return [name for name, count in counter.items() if count > 1]


def validate_gpio_module_names(config, module_section, io_sections):
    module_names = {x["name"] for x in config.get(module_section, [])}
    bad_configs = {}

    for io_section in io_sections:
        for io_conf in config.get(io_section, []):
            if io_conf["module"] not in module_names:
                bad_configs.setdefault(io_section, {})[
                    io_conf["name"]
                ] = "%s section has no module configured with the name '%s'" % (
                    module_section,
                    io_conf["module"],
                )

    return bad_configs


def _read_config(path):
    """
    Loads a yaml file from the file system and returns it as as dict.
    :param path: The filesystem path
    :type path: str
    :return: The config
    :rtype: dict
    """
    with open(path) as f:
        return yaml.safe_load(f)


def get_main_schema():
    """
    Load the main config schema from the yaml file packaged in the same dir as this file.
    :return: Config schema
    :rtype: dict
    """
    schema_path = join(dirname(realpath(__file__)), "config.schema.yml")
    return yaml.safe_load(open(schema_path))


def validate_and_normalise_config(
    config: Dict[str, Any], schema: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Validate the config dict based on the config schema.
    :param config: The supplied configuration
    :type config: dict
    :param schema: The schema against which to validate the config
    :type schema: dict
    :return: Normalised config
    :rtype: dict
    """
    validator = ConfigValidator(schema)
    if not validator.validate(config):
        raise ConfigValidationFailed(
            "Config did not validate:\n%s" % yaml.dump(validator.errors)
        )
    config = validator.normalized(config)

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

    bad_configs = {}

    # Make sure each of the IO configs refer to an existing module config
    module_and_io_sections = dict(
        gpio_modules=("digital_inputs", "digital_outputs"),
        sensor_modules=("sensor_inputs",),
        stream_modules=("stream_reads", "stream_writes"),
    )
    for module_section, io_sections in module_and_io_sections.items():
        bad_configs.update(
            validate_gpio_module_names(config, module_section, io_sections)
        )

    if bad_configs:
        raise ConfigValidationFailed(
            "Config did not validate due to errors in the following sections:\n%s"
            % yaml.dump(bad_configs)
        )
    return config


def load_main_config(path):
    """
    Read the main config file from the given path, validate it and return it normalised.
    :param path: The filesystem path
    :type path: str
    :return: The config
    :rtype: dict
    """
    return validate_and_normalise_config(_read_config(path), get_main_schema())


def validate_and_normalise_sensor_input_config(config, module):
    schema = get_main_schema()
    sensor_input_schema = schema["sensor_inputs"]["schema"]["schema"].copy()
    sensor_input_schema.update(getattr(module, "SENSOR_SCHEMA", {}))
    return validate_and_normalise_config(config, sensor_input_schema)
