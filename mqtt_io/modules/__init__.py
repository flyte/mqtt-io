"""
Contains stuff useful across all modules, whether they're GPIO, sensor or stream ones.
"""

import logging
import sys
from subprocess import CalledProcessError, check_call
from types import ModuleType

import pkg_resources

from ..exceptions import CannotInstallModuleRequirements

_LOG = logging.getLogger(__name__)


def install_missing_requirements(module: ModuleType) -> None:
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
        _LOG.debug("Module %r has no extra requirements to install.", module)
        return

    pkgs_installed = pkg_resources.WorkingSet()
    pkgs_required = []
    for req in reqs:
        if pkgs_installed.find(pkg_resources.Requirement.parse(req)) is None:
            pkgs_required.append(req)

    if not pkgs_required:
        _LOG.debug("Module %r has all of its requirements installed already.", module)
        return

    try:
        check_call([sys.executable, "-m", "pip", "install"] + pkgs_required)
    except CalledProcessError as err:
        raise CannotInstallModuleRequirements(
            "Unable to install packages for module %r (%s): %s"
            % (module, pkgs_required, err)
        ) from err
