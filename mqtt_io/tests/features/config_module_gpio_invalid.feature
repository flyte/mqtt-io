Feature: Invalid GPIO module config validation
    Scenario: Mock GPIO adapter should not accept any extra values not listed in PIN_CONFIG etc.
        Given a valid config
        And the config has an entry in gpio_modules with
            """
            name: mock
            module: mock
            """
        And the config has an entry in digital_inputs with
            """
            name: mock0
            module: mock
            pin: 0
            doesntexist: true
            """
        When we validate the main config
        And we instantiate MqttIo
        And we initialise GPIO modules
        And we initialise digital_inputs
        Then config validation fails
