import pytest
import trio

from mqtt_io.server import MQTTIO

from ..config import validate_and_normalise_main_config
from ..exceptions import ConfigValidationFailed
from .conftest import ConfigBuilder


async def test_mock_gpio_adapter_should_not_accept_any_extra_values_not_listed_in_pin_config_etc_(
    nursery: trio.Nursery,
    config_builder: ConfigBuilder,
) -> None:
    """
    Mock GPIO adapter should not accept any extra values not listed in PIN_CONFIG etc.
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
        doesntexist: true
        """,
    )
    config = validate_and_normalise_main_config(config_builder.config)
    mqttio = MQTTIO(config)
    with pytest.raises(ConfigValidationFailed):
        await nursery.start(mqttio.run_async)
