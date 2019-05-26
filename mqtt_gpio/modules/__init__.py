import logging

from ..exceptions import CannotInstallModuleRequirements

_LOG = logging.getLogger(__name__)

BASE_SCHEMA = {
    "name": dict(required=True, empty=False),
    "module": dict(required=True, empty=False),
    "cleanup": dict(required=False, type="boolean", default=True),
}


def install_missing_requirements(module):
    """
    Some of the modules require external packages to be installed. This gets
    the list from the `REQUIREMENTS` module attribute and attempts to
    install the requirements using pip.
    :param module: GPIO module
    :type module: ModuleType
    :return: None
    :rtype: NoneType
    """
    reqs = getattr(module, "REQUIREMENTS", [])
    if not reqs:
        _LOG.info("Module %r has no extra requirements to install." % module)
        return
    import pkg_resources

    pkgs_installed = pkg_resources.WorkingSet()
    pkgs_required = []
    for req in reqs:
        if pkgs_installed.find(pkg_resources.Requirement.parse(req)) is None:
            pkgs_required.append(req)
    if pkgs_required:
        from subprocess import check_call, CalledProcessError

        try:
            check_call(["/usr/bin/env", "pip", "install"] + pkgs_required)
        except CalledProcessError as err:
            raise CannotInstallModuleRequirements(
                "Unable to install packages for module %r (%s): %s"
                % (module, pkgs_required, err)
            )
