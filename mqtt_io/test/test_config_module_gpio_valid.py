import trio

from mqtt_io.server import MQTTIO

from ..config import validate_and_normalise_main_config
from .conftest import ConfigBuilder


async def test_mock_gpio_adapter_s_pin_config__test__value_should_be_accepted(
    nursery: trio.Nursery,
    config_builder: ConfigBuilder,
) -> None:
    """
    Mock GPIO adapter's PIN_CONFIG "test" value should be accepted
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
        test: true
        """,
    )
    config = validate_and_normalise_main_config(config_builder.config)
    mqttio = MQTTIO(config)
    await nursery.start(mqttio.run_async)
