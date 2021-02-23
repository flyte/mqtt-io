Feature: GPIO module runtime
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

    Scenario: Polled digital input fires remote interrupt if lock is not already acquired
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
            interrupt: falling
            """
        And the config has an entry in digital_inputs with
            """
            name: mock1
            module: mock
            pin: 1
            interrupt: falling
            interrupt_for:
            - mock0
            """
        When we validate the main config
        And we instantiate MqttIo
        And we initialise GPIO modules
        And we initialise digital inputs
        And we mock handle_remote_interrupt on MqttIo
        And mock1 reads a value of false with a last value of true
        Then handle_remote_interrupt on MqttIo should be called with
            """
            args:
              0: ["mock0"]
            """
        And interrupt lock for mock1 should be locked

    Scenario: Polled digital input does not fire remote interrupt if lock is already acquired
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
            interrupt: falling
            """
        And the config has an entry in digital_inputs with
            """
            name: mock1
            module: mock
            pin: 1
            interrupt: falling
            interrupt_for:
            - mock0
            """
        When we validate the main config
        And we instantiate MqttIo
        And we initialise GPIO modules
        And we initialise digital inputs
        And we mock handle_remote_interrupt on MqttIo
        And we lock interrupt lock for mock1
        And mock1 reads a value of false with a last value of true
        Then handle_remote_interrupt on MqttIo should not be called
