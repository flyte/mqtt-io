from unittest.mock import Mock

from .. import GenericSensor

REQUIREMENTS = ()
CONFIG_SCHEMA = dict(test=dict(type="boolean", required=False, default=False))


class Sensor(GenericSensor):
    setup_module = Mock()
    setup_sensor = Mock()
    get_value = Mock(return_value=1)
