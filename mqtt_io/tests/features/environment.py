import asyncio
from typing import Any


# fixture of event handler that calls a mock, so we can see if an event has been called


def before_scenario(context: Any, scenario: Any) -> None:
    """
    Initialise data.
    """
    context.loop = asyncio.new_event_loop()
    context.data = dict(
        raw_config={},
        loop=context.loop,
        transient_tasks=[],
        event_subs={},
        mocks={},
    )


def after_scenario(context: Any, scenario: Any) -> None:
    """
    Shut down asyncio loop cleanly.
    """
    loop: asyncio.AbstractEventLoop = context.loop
    try:
        mqttio = context.data["mqttio"]
    except (KeyError, AttributeError):
        pass
    else:
        loop.run_until_complete(mqttio.shutdown())
    loop.close()
