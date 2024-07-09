"""
Shared types and utils for validation functions.
"""

from typing import Dict, List


BadConfigsType = Dict[str, Dict[str, List[str]]]


def add_error(
    bad_configs: BadConfigsType,
    section: str,
    subsection: str,
    error: str,
) -> None:
    """
    Add an error to the given section and subsection of bad_configs.
    """
    bad_configs.setdefault(section, {}).setdefault(subsection, []).append(error)
