Feature: Tests for the successful initialisation of the Sensor aspects of the server
    Scenario: Successful initialisation of mock Sensor module
        Given a valid config
        And the config has an entry in sensor_modules with
            """
            name: mock
            module: mock
            test: true
            """
        And the config has an entry in sensor_inputs with
            """
            name: mock0
            module: mock
            pin: 0
            """
        When we validate the main config
        And we instantiate MqttIo
        And we initialise sensor modules
        Then sensor module mock should be initialised
        And sensor module mock should have 1 call(s) to setup_module
        And sensor config mock should contain
            """
            test: true
            """
