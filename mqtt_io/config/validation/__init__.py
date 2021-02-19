from typing import Dict, List


BadConfigsType = Dict[str, Dict[str, List[str]]]


def add_error(
    bad_configs: BadConfigsType,
    section: str,
    subsection: str,
    error: str,
) -> None:
    bad_configs.setdefault(section, {}).setdefault(subsection, []).append(error)
