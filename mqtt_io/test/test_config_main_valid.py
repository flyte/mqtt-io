import pytest

from ..config import validate_and_normalise_main_config
from .conftest import ConfigBuilder


def test_mqtt_section_with_host_should_pass(config_builder: ConfigBuilder) -> None:
    """
    MQTT section with host should pass
    """
    config_builder.add_minimal_config()
    validate_and_normalise_main_config(config_builder.config)


def test_gpio_module_with_digital_input_and_digital_output_should_validate(
    config_builder: ConfigBuilder,
) -> None:
    """
    GPIO module with digital_input and digital_output should validate
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
    config_builder.add_list_section_entry(
        "digital_inputs",
        """
        name: mock1
        module: mock
        pin: 1
        """,
    )
    validate_and_normalise_main_config(config_builder.config)


def test_the_same_pin_number_used_across_different_modules_should_validate(
    config_builder: ConfigBuilder,
) -> None:
    """
    The same pin number used across different modules should validate
    """
    config_builder.add_minimal_config()
    config_builder.add_list_section_entry(
        "gpio_modules",
        """
        name: mockA
        module: mock
        """,
    )
    config_builder.add_list_section_entry(
        "gpio_modules",
        """
        name: mockB
        module: mock
        """,
    )
    config_builder.add_list_section_entry(
        "digital_inputs",
        """
        name: mock0A
        module: mockA
        pin: 0
        """,
    )
    config_builder.add_list_section_entry(
        "digital_inputs",
        """
        name: mock0B
        module: mockB
        pin: 0
        """,
    )
    validate_and_normalise_main_config(config_builder.config)


@pytest.mark.parametrize("section_name", ("digital_inputs", "digital_outputs"))
def test_a_gpio_module_with_a_single_config_in__section__should_validate(
    config_builder: ConfigBuilder, section_name: str
) -> None:
    """
    A GPIO module with a single config in <section> should validate
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
        section_name,
        """
        name: mock0
        module: mock
        pin: 0
        """,
    )
    validate_and_normalise_main_config(config_builder.config)
