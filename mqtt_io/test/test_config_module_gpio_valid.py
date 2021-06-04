from pytest_bdd import scenario  # type: ignore


@scenario(
    "features/config_module_gpio_valid.feature",
    'Mock GPIO adapter\'s PIN_CONFIG "test" value should be accepted',
)
def test_mock_gpio_adapter_s_pin_config__test__value_should_be_accepted() -> None:
    """
    Mock GPIO adapter's PIN_CONFIG "test" value should be accepted
    """
    pass
