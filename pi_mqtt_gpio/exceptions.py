class CannotInstallModuleRequirements(Exception):
    pass


class InvalidPayload(Exception):
    pass


class ConfigInvalid(Exception):
    def __init__(self, errors, *args, **kwargs):
        self.errors = errors
        super(ConfigInvalid, self).__init__(errors, *args, **kwargs)


class ModuleConfigInvalid(ConfigInvalid):
    pass
