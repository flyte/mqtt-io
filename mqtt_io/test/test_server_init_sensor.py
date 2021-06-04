from pytest_bdd import scenario  # type: ignore


@scenario(
    "features/server_init_sensor.feature",
    "Successful initialisation of mock Sensor module",
)
def test_successful_initialisation_of_mock_sensor_module() -> None:
    """
    Successful initialisation of mock Sensor module
    """
    pass
