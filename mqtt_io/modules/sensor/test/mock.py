"""
Mock Sensor module for use with the tests.
"""

from unittest.mock import Mock

from .. import GenericSensor

REQUIREMENTS = ()
CONFIG_SCHEMA = dict(test=dict(type="boolean", required=False, default=False))


class Sensor(GenericSensor):
    """
    Mock Sensor class for use with the tests.
    """

    setup_module = Mock()
    setup_sensor = Mock()
    get_value = Mock(return_value=1)
