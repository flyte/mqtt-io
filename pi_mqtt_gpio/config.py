import yaml
import cerberus

from . import CONFIG_SCHEMA
from .exceptions import ConfigInvalid


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


class PiMqttGpioConfig(object):
    def __init__(self, config):
        """
        Validate and normalize the config. If valid, initialise the object with
        the config values.

        :param config: Configuration values as a dict
        :type config: dict
        """
        validator = ConfigValidator(CONFIG_SCHEMA)
        if not validator.validate(config):
            raise ConfigInvalid(validator.errors)
        self.__dict__.update(validator.normalized(config))

    @classmethod
    def from_yaml_file(cls, path):
        """
        Load a YAML configuration file and return a PiMqttGpioConfig object.

        :param path: The path to a config file containing YAML.
        :type path: str
        :return: A validated and normalized PiMqttGpioConfig object.
        :rtype: PiMqttGpioConfig
        """
        with open(path) as f:
            return cls(yaml.load(f))
