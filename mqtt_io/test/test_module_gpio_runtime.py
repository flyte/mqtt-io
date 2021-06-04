from pytest_bdd import scenario  # type: ignore


@scenario(
    "features/module_gpio_runtime.feature",
    "Polled digital input fires DigitalInputChangedEvent on changes",
)
def test_polled_digital_input_fires_digitalinputchangedevent_on_changes() -> None:
    """
    Polled digital input fires DigitalInputChangedEvent on changes
    """
    pass


@scenario(
    "features/module_gpio_runtime.feature",
    "Polled digital input fires remote interrupt if lock is not already acquired",
)
def test_polled_digital_input_fires_remote_interrupt_if_lock_is_not_already_acquired() -> None:
    """
    Polled digital input fires remote interrupt if lock is not already acquired
    """
    pass


@scenario(
    "features/module_gpio_runtime.feature",
    "Polled digital input does not fire remote interrupt if lock is already acquired",
)
def test_polled_digital_input_does_not_fire_remote_interrupt_if_lock_is_already_acquired() -> None:
    """
    Polled digital input does not fire remote interrupt if lock is already acquired
    """
    pass


@scenario(
    "features/module_gpio_runtime.feature",
    "Non-inverted value is published on DigitalInputChangedEvent to_value True",
)
def test_non_inverted_value_is_published_on_digitalinputchangedevent_to_value_true() -> None:
    """
    Non-inverted value is published on DigitalInputChangedEvent to_value True
    """
    pass


@scenario(
    "features/module_gpio_runtime.feature",
    "Non-inverted value is published on DigitalInputChangedEvent to_value True when interrupt comes from other thread",
)
def test_non_inverted_value_is_published_on_digitalinputchangedevent_to_value_true_when_interrupt_comes_from_other_thread() -> None:
    """
    Non-inverted value is published on DigitalInputChangedEvent to_value True when interrupt comes from other thread
    """
    pass


@scenario(
    "features/module_gpio_runtime.feature",
    "Inverted value is published on DigitalInputChangedEvent to_value True",
)
def test_inverted_value_is_published_on_digitalinputchangedevent_to_value_true() -> None:
    """
    Inverted value is published on DigitalInputChangedEvent to_value True
    """
    pass


@scenario(
    "features/module_gpio_runtime.feature",
    "Non-inverted value is published on DigitalInputChangedEvent to_value False",
)
def test_non_inverted_value_is_published_on_digitalinputchangedevent_to_value_false() -> None:
    """
    Non-inverted value is published on DigitalInputChangedEvent to_value False
    """
    pass


@scenario(
    "features/module_gpio_runtime.feature",
    "Inverted value is published on DigitalInputChangedEvent to_value False",
)
def test_inverted_value_is_published_on_digitalinputchangedevent_to_value_false() -> None:
    """
    Inverted value is published on DigitalInputChangedEvent to_value False
    """
    pass
