import asyncio

from collections import namedtuple

import logging

_LOG = logging.getLogger(__name__)
_LOG.addHandler(logging.StreamHandler())
_LOG.setLevel(logging.DEBUG)

DigitalInputChangedEvent = namedtuple(
    "DigitalInputChangedEvent", ("input_name", "from_value", "to_value")
)

DigitalOutputChangedEvent = namedtuple("DigitalOutputChangedEvent", ("output_name"))


async def digital_input_poller(event_bus, module, input_config):
    last_value = None
    while True:
        value = await module.async_get_pin(input_config["pin"])
        if value != last_value:
            _LOG.debug("Firing event...")
            event_bus.fire(
                DigitalInputChangedEvent(input_config["name"], last_value, value)
            )
            _LOG.debug("After event fired.")
            last_value = value
        # TODO: Tasks pending completion -@flyte at 29/05/2019, 01:02:50
        # Make this delay configurable in input_config
        await asyncio.sleep(0.1)

