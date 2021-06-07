import trio
import trio.testing

from mqtt_io.events import DigitalInputChangedEvent
from mqtt_io.server import MQTTIO

from ..config import validate_and_normalise_main_config
from .conftest import ConfigBuilder, pin_reads_value


async def test_polled_digital_input_fires_digitalinputchangedevent_on_changes(
    nursery: trio.Nursery,
    config_builder: ConfigBuilder,
) -> None:
    """
    Polled digital input fires DigitalInputChangedEvent on changes
    """
    config_builder.add_minimal_config()
    config_builder.add_list_section_entry(
        "gpio_modules",
        """
        name: mock
        module: mock
        """,
    )
    config_builder.add_list_section_entry(
        "digital_inputs",
        """
        name: mock0
        module: mock
        pin: 0
        """,
    )
    config = validate_and_normalise_main_config(config_builder.config)
    mqttio = MQTTIO(config)
    await nursery.start(mqttio.run_async)
    async with await mqttio.event_bus.subscribe(DigitalInputChangedEvent, 1) as event_rx:
        await pin_reads_value(mqttio, "mock0", False, True)
        await trio.testing.wait_all_tasks_blocked()
        try:
            assert event_rx.receive_nowait()
        except trio.WouldBlock as exc:
            raise Exception("No events fired") from exc


def test_polled_digital_input_fires_remote_interrupt_if_lock_is_not_already_acquired(
    config_builder: ConfigBuilder,
) -> None:
    """
    Polled digital input fires remote interrupt if lock is not already acquired
    """
    config_builder.add_minimal_config()


def test_polled_digital_input_does_not_fire_remote_interrupt_if_lock_is_already_acquired(
    config_builder: ConfigBuilder,
) -> None:
    """
    Polled digital input does not fire remote interrupt if lock is already acquired
    """
    config_builder.add_minimal_config()


def test_non_inverted_value_is_published_on_digitalinputchangedevent_to_value_true(
    config_builder: ConfigBuilder,
) -> None:
    """
    Non-inverted value is published on DigitalInputChangedEvent to_value True
    """
    config_builder.add_minimal_config()


def test_non_inverted_value_is_published_on_digitalinputchangedevent_to_value_true_when_interrupt_comes_from_other_thread(
    config_builder: ConfigBuilder,
) -> None:
    """
    Non-inverted value is published on DigitalInputChangedEvent to_value True when interrupt comes from other thread
    """
    config_builder.add_minimal_config()


def test_inverted_value_is_published_on_digitalinputchangedevent_to_value_true(
    config_builder: ConfigBuilder,
) -> None:
    """
    Inverted value is published on DigitalInputChangedEvent to_value True
    """
    config_builder.add_minimal_config()


def test_non_inverted_value_is_published_on_digitalinputchangedevent_to_value_false(
    config_builder: ConfigBuilder,
) -> None:
    """
    Non-inverted value is published on DigitalInputChangedEvent to_value False
    """
    config_builder.add_minimal_config()


def test_inverted_value_is_published_on_digitalinputchangedevent_to_value_false(
    config_builder: ConfigBuilder,
) -> None:
    """
    Inverted value is published on DigitalInputChangedEvent to_value False
    """
    config_builder.add_minimal_config()
