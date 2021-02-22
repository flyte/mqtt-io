import asyncio
from typing import Any


def before_scenario(context: Any, scenario: Any) -> None:
    """
    Initialise data.
    """
    context.data = dict(raw_config={}, loop=asyncio.new_event_loop())


def after_scenario(context: Any, scenario: Any) -> None:
    """
    Shut down asyncio loop cleanly.
    """
    loop = context.data["loop"]
    try:
        mqttio = context.data["mqttio"]
    except (KeyError, AttributeError):
        pass
    else:
        loop.run_until_complete(mqttio.shutdown())
    loop.stop()
    loop.close()
