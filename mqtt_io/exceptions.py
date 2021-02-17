class ConfigError(Exception):
    pass


class ConfigValidationFailed(ConfigError):
    pass


class RuntimeConfigError(ConfigError):
    pass


class CannotInstallModuleRequirements(Exception):
    pass


class InvalidPayload(Exception):
    pass
