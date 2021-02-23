Feature: GPIO module runtime
    @wip
    Scenario: Polled digital input fires DigitalInputChangedEvent on changes
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
            """
        When we validate the main config
        And we instantiate MqttIo
        And we subscribe to DigitalInputChangedEvent
        And we initialise GPIO modules
        And we initialise digital inputs
        And mock0 reads a value of false with a last value of true
        Then DigitalInputChangedEvent is fired with
            """
            input_name: mock0
            from_value: true
            to_value: false
            """
