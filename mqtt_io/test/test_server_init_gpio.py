from pytest_bdd import scenario  # type: ignore


@scenario(
    "features/server_init_gpio.feature", "Successful initialisation of mock GPIO module"
)
def test_successful_initialisation_of_mock_gpio_module() -> None:
    """
    Successful initialisation of mock GPIO module
    """
    pass


@scenario("features/server_init_gpio.feature", "Initialising a polled digital input")
def test_initialising_a_polled_digital_input() -> None:
    """
    Initialising a polled digital input
    """
    pass


@scenario(
    "features/server_init_gpio.feature", "Initialising an interrupt digital input"
)
def test_initialising_an_interrupt_digital_input() -> None:
    """
    Initialising an interrupt digital input
    """
    pass


@scenario(
    "features/server_init_gpio.feature",
    "Initialising an interrupt digital input for another pin",
)
def test_initialising_an_interrupt_digital_input_for_another_pin() -> None:
    """
    Initialising an interrupt digital input for another pin
    """
    pass


@scenario("features/server_init_gpio.feature", "Initialising a digital output")
def test_initialising_a_digital_output() -> None:
    """
    Initialising a digital output
    """
    pass


@scenario(
    "features/server_init_gpio.feature",
    "Digital output publishes initial high/on value when publish_initial=True",
)
def test_digital_output_publishes_initial_high_on_value_when_publish_initial_true() -> None:
    """
    Digital output publishes initial high/on value when publish_initial=True
    """
    pass


@scenario(
    "features/server_init_gpio.feature",
    "Digital output publishes initial low/off value when publish_initial=True",
)
def test_digital_output_publishes_initial_low_off_value_when_publish_initial_true() -> None:
    """
    Digital output publishes initial low/off value when publish_initial=True
    """
    pass


@scenario(
    "features/server_init_gpio.feature",
    "Inverted digital output publishes initial high/off value when publish_initial=True",
)
def test_inverted_digital_output_publishes_initial_high_off_value_when_publish_initial_true() -> None:
    """
    Inverted digital output publishes initial high/off value when publish_initial=True
    """
    pass


@scenario(
    "features/server_init_gpio.feature",
    "Inverted digital output publishes initial low/on value when publish_initial=True",
)
def test_inverted_digital_output_publishes_initial_low_on_value_when_publish_initial_true() -> None:
    """
    Inverted digital output publishes initial low/on value when publish_initial=True
    """
    pass


@scenario(
    "features/server_init_gpio.feature", "Digital output publishes ON when turned on"
)
def test_digital_output_publishes_on_when_turned_on() -> None:
    """
    Digital output publishes ON when turned on
    """
    pass


@scenario(
    "features/server_init_gpio.feature", "Digital output publishes OFF when turned off"
)
def test_digital_output_publishes_off_when_turned_off() -> None:
    """
    Digital output publishes OFF when turned off
    """
    pass


@scenario(
    "features/server_init_gpio.feature",
    "Inverted digital output publishes ON when turned on",
)
def test_inverted_digital_output_publishes_on_when_turned_on() -> None:
    """
    Inverted digital output publishes ON when turned on
    """
    pass


@scenario(
    "features/server_init_gpio.feature",
    "Inverted digital output publishes OFF when turned off",
)
def test_inverted_digital_output_publishes_off_when_turned_off() -> None:
    """
    Inverted digital output publishes OFF when turned off
    """
    pass
