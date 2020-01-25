from os.path import realpath, dirname, join
import logging

import cerberus
import yaml

from .exceptions import ConfigValidationFailed


_LOG = logging.getLogger(__name__)


class ConfigValidator(cerberus.Validator):
    """
    Cerberus Validator containing function(s) for use with validating or
    coercing values relevant to the pi_mqtt_gpio project.
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


def _get_main_schema():
    """
    Load the main config schema from the yaml file packaged in the same dir as this file.
    :return: Config schema
    :rtype: dict
    """
    schema_path = join(dirname(realpath(__file__)), "config.schema.yml")
    return yaml.safe_load(open(schema_path))


def validate_and_normalise_config(config, schema):
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
    return validator.normalized(config)


def load_main_config(path):
    """
    Read the main config file from the given path, validate it and return it normalised.
    :param path: The filesystem path
    :type path: str
    :return: The config
    :rtype: dict
    """
    return validate_and_normalise_config(_read_config(path), _get_main_schema())

