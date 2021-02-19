"""
Utility functions for the tests.
"""

import yaml

from ..config import validate_and_normalise_main_config
from ..types import ConfigType


def validate_config(yaml_config: str) -> ConfigType:
    """
    Load and validate the provided config.
    """
    return validate_and_normalise_main_config(yaml.safe_load(yaml_config))
