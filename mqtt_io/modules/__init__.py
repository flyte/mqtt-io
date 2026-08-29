"""
Contains stuff useful across all modules, whether they're GPIO, sensor or stream ones.
"""

import logging
import sys
from subprocess import CalledProcessError, check_call
from types import ModuleType
from typing import List

from importlib.metadata import PackageNotFoundError, version

from packaging.requirements import Requirement

from ..exceptions import CannotInstallModuleRequirements

_LOG = logging.getLogger(__name__)


def install_missing_requirements(pkgs_required: List[str]) -> None:
    """
    Use pip to install the list of requirements.
    """
    check_call([sys.executable, "-m", "pip", "install"] + pkgs_required)


def install_missing_module_requirements(module: ModuleType) -> None:
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

    pkgs_required = []
    for req in reqs:
        requirement = Requirement(req)
        try:
            installed = version(requirement.name)
        except PackageNotFoundError:
            pkgs_required.append(req)
            continue
        if requirement.specifier and installed not in requirement.specifier:
            pkgs_required.append(req)

    if not pkgs_required:
        _LOG.debug("Module %r has all of its requirements installed already.", module)
        return

    try:
        install_missing_requirements(pkgs_required)
    except CalledProcessError as err:
        raise CannotInstallModuleRequirements(
            "Unable to install packages for module %r (%s): %s"
            % (module, pkgs_required, err)
        ) from err
