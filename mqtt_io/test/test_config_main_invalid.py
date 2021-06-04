import pytest

from ..config import validate_and_normalise_main_config
from ..exceptions import ConfigValidationFailed
from .conftest import ConfigBuilder


def test_missing_mqtt_section_should_fail(config_builder: ConfigBuilder) -> None:
    """
    Missing MQTT section should fail
    """
    # Just add the gpio_modules section without the mqtt one
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
    with pytest.raises(ConfigValidationFailed):
        validate_and_normalise_main_config(config_builder.config)


def test_missing_mqtt_host_should_fail(config_builder: ConfigBuilder) -> None:
    """
    Missing MQTT host should fail
    """
    config_builder.add_toplevel_section("mqtt", "{}")
    with pytest.raises(ConfigValidationFailed):
        validate_and_normalise_main_config(config_builder.config)


def test_digital_input_with_no_existing_module_should_fail(
    config_builder: ConfigBuilder,
) -> None:
    """
    Digital input with no existing module should fail
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
        module: doesntexist
        pin: 1
        """,
    )
    with pytest.raises(ConfigValidationFailed):
        validate_and_normalise_main_config(config_builder.config)


def test_digital_output_with_no_existing_module_should_fail(
    config_builder: ConfigBuilder,
) -> None:
    """
    Digital output with no existing module should fail
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
        "digital_outputs",
        """
        name: mock0
        module: mock
        pin: 0
        """,
    )
    config_builder.add_list_section_entry(
        "digital_outputs",
        """
        name: mock1
        module: doesntexist
        pin: 1
        """,
    )
    with pytest.raises(ConfigValidationFailed):
        validate_and_normalise_main_config(config_builder.config)


def test_two_gpio_modules_with_the_same_name_should_fail(
    config_builder: ConfigBuilder,
) -> None:
    """
    Two GPIO modules with the same name should fail
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
        "gpio_modules",
        """
        name: mock
        module: mock
        """,
    )
    with pytest.raises(ConfigValidationFailed):
        validate_and_normalise_main_config(config_builder.config)


def test_gpio_modules_without_digital_inputs_or_digital_outputs_should_fail(
    config_builder: ConfigBuilder,
) -> None:
    """
    GPIO modules without digital_inputs or digital_outputs should fail
    """
    config_builder.add_minimal_config()
    config_builder.add_list_section_entry(
        "gpio_modules",
        """
        name: mock
        module: mock
        """,
    )
    with pytest.raises(ConfigValidationFailed):
        validate_and_normalise_main_config(config_builder.config)


@pytest.mark.skip(
    reason="Some modules, such as the PiFaceDigitalIO2 reuse pin numbers for in/outputs"
)
def test_configuring_a_gpio_module_s_pin_as_a_digital_input_twice_should_fail(
    config_builder: ConfigBuilder,
) -> None:
    """
    Configuring a GPIO module's pin as a digital input twice should fail
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
        pin: 0
        """,
    )
    with pytest.raises(ConfigValidationFailed):
        validate_and_normalise_main_config(config_builder.config)


@pytest.mark.skip(
    reason="Some modules, such as the PiFaceDigitalIO2 reuse pin numbers for in/outputs"
)
def test_configuring_a_gpio_module_s_pin_as_a_digital_output_twice_should_fail(
    config_builder: ConfigBuilder,
) -> None:
    """
    Configuring a GPIO module's pin as a digital output twice should fail
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
        "digital_outputs",
        """
        name: mock0
        module: mock
        pin: 0
        """,
    )
    config_builder.add_list_section_entry(
        "digital_outputs",
        """
        name: mock1
        module: mock
        pin: 0
        """,
    )
    with pytest.raises(ConfigValidationFailed):
        validate_and_normalise_main_config(config_builder.config)


@pytest.mark.skip(
    reason="Some modules, such as the PiFaceDigitalIO2 reuse pin numbers for in/outputs"
)
def test_configuring_a_gpio_module_s_pin_as_a_digital_output_and_a_digital_input_should_fail(
    config_builder: ConfigBuilder,
) -> None:
    """
    Configuring a GPIO module's pin as a digital output and a digital input should fail
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
        "digital_outputs",
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
        pin: 0
        """,
    )
    with pytest.raises(ConfigValidationFailed):
        validate_and_normalise_main_config(config_builder.config)


@pytest.mark.parametrize("section_name", ("digital_inputs", "digital_outputs"))
def test_using_the_same_name_for_two_sections_should_not_validate(
    config_builder: ConfigBuilder, section_name: str
) -> None:
    """
    Using the same name for two sections should not validate
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
    config_builder.add_list_section_entry(
        section_name,
        """
        name: mock0
        module: mock
        pin: 1
        """,
    )
    with pytest.raises(ConfigValidationFailed):
        validate_and_normalise_main_config(config_builder.config)


def test_using_a_pin_that_s_not_configured_as_an_interrupt_in_an_interrupt_for_list_should_not_validate(
    config_builder: ConfigBuilder,
) -> None:
    """
    Using a pin that's not configured as an interrupt in an interrupt_for list should not validate
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
        interrupt: rising
        interrupt_for:
        - mock0
        """,
    )
    with pytest.raises(ConfigValidationFailed):
        validate_and_normalise_main_config(config_builder.config)


def test_configuring_a_pin_as_an_interrupt_for_another_pin_without_making_it_an_interrupt_itself_should_not_validate(
    config_builder: ConfigBuilder,
) -> None:
    """
    Configuring a pin as an interrupt_for another pin without making it an interrupt itself should not validate
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
        interrupt: rising
        """,
    )
    config_builder.add_list_section_entry(
        "digital_inputs",
        """
        name: mock1
        module: mock
        pin: 1
        interrupt_for:
        - mock0
        """,
    )
    with pytest.raises(ConfigValidationFailed):
        validate_and_normalise_main_config(config_builder.config)


def test_configuring_a_pin_as_an_interrupt_for_itself_should_not_validate(
    config_builder: ConfigBuilder,
) -> None:
    """
    Configuring a pin as an interrupt_for itself should not validate
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
        name: mock1
        module: mock
        pin: 1
        interrupt_for:
        - mock1
        """,
    )
    with pytest.raises(ConfigValidationFailed):
        validate_and_normalise_main_config(config_builder.config)
