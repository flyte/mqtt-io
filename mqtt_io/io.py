import asyncio

from collections import namedtuple

import logging

_LOG = logging.getLogger(__name__)

DigitalInputChangedEvent = namedtuple(
    "DigitalInputChangedEvent", ("input_name", "from_value", "to_value")
)
DigitalOutputChangedEvent = namedtuple(
    "DigitalOutputChangedEvent", ("output_name", "to_value")
)
# IDEA: Possible implementations -@flyte at 25/01/2020, 00:26:44
# Do we really want Sensor stuff in io.py? Probably not.
# Do we really want events to be spread across different modules? Leaning towards yes.
SensorReadEvent = namedtuple("SensorReadEvent", ("sensor_name", "value"))
