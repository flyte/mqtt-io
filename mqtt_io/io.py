import asyncio

from collections import namedtuple

import logging

_LOG = logging.getLogger(__name__)

DigitalInputChangedEvent = namedtuple(
    "DigitalInputChangedEvent", ("input_name", "from_value", "to_value")
)
DigitalOutputChangedEvent = namedtuple("DigitalOutputChangedEvent", ("output_name"))
# IDEA: Possible implementations -@flyte at 25/01/2020, 00:26:44
# Do we really want Sensor stuff in io.py? Probably not.
# Do we really want events to be spread across different modules? Leaning towards yes.
SensorReadEvent = namedtuple("SensorReadEvent", ("sensor_name", "value"))


async def digital_input_poller(event_bus, module, input_config):
    last_value = None
    while True:
        value = await module.async_get_pin(input_config["pin"])
        if value != last_value:
            _LOG.info(
                "Digital input '%s' value changed to %s", input_config["name"], value
            )
            event_bus.fire(
                DigitalInputChangedEvent(input_config["name"], last_value, value)
            )
            last_value = value
        # TODO: Tasks pending completion -@flyte at 29/05/2019, 01:02:50
        # Make this delay configurable in input_config
        await asyncio.sleep(0.1)

