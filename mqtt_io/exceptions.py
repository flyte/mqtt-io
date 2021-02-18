"""
Exceptions thrown by MQTT IO.
"""


class ConfigError(Exception):
    """
    Base class for any error raised because of a problem with the config file.
    """


class ConfigValidationFailed(ConfigError):
    """
    The config file validation failed.
    """


class RuntimeConfigError(ConfigError):
    """
    Something in the config file turned out to be unusable at runtime.
    """


class CannotInstallModuleRequirements(Exception):
    """
    Installing the Python requirements for a module using pip failed.
    """
