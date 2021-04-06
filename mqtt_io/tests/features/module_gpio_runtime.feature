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
        Then handle_remote_interrupt on MqttIo shouldn't be called

    Scenario: Non-inverted value is published on DigitalInputChangedEvent to_value True
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
        And we initialise GPIO modules
        And we initialise digital inputs
        # Mock this to stop the digital_input_poller from firing events too
        And we mock _handle_digital_input_value on MqttIo
        And we mock _mqtt_publish on MqttIo
        And we fire a new DigitalInputChangedEvent event with
            """
            input_name: mock0
            from_value: false
            to_value: true
            """
        Then _mqtt_publish on MqttIo should be called with MQTT message
            """
            payload: "ON"
            """

    Scenario: Non-inverted value is published on DigitalInputChangedEvent to_value True when interrupt comes from other thread
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
        And we initialise GPIO modules
        And we initialise digital inputs
        # Mock this to stop the digital_input_poller from firing events too
        And we mock _handle_digital_input_value on MqttIo
        And we mock _mqtt_publish on MqttIo
        And we fire a new DigitalInputChangedEvent event from another thread with
            """
            input_name: mock0
            from_value: false
            to_value: true
            """
        Then _mqtt_publish on MqttIo should be called with MQTT message
            """
            payload: "ON"
            """

    Scenario: Inverted value is published on DigitalInputChangedEvent to_value True
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
            inverted: yes
            """
        When we validate the main config
        And we instantiate MqttIo
        And we initialise GPIO modules
        And we initialise digital inputs
        # Mock this to stop the digital_input_poller from firing events too
        And we mock _handle_digital_input_value on MqttIo
        And we mock _mqtt_publish on MqttIo
        And we fire a new DigitalInputChangedEvent event with
            """
            input_name: mock0
            from_value: false
            to_value: true
            """
        Then _mqtt_publish on MqttIo should be called with MQTT message
            """
            payload: "OFF"
            """

    Scenario: Non-inverted value is published on DigitalInputChangedEvent to_value False
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
        And we initialise GPIO modules
        And we initialise digital inputs
        # Mock this to stop the digital_input_poller from firing events too
        And we mock _handle_digital_input_value on MqttIo
        And we mock _mqtt_publish on MqttIo
        And we fire a new DigitalInputChangedEvent event with
            """
            input_name: mock0
            from_value: true
            to_value: false
            """
        Then _mqtt_publish on MqttIo should be called with MQTT message
            """
            payload: "OFF"
            """

    Scenario: Inverted value is published on DigitalInputChangedEvent to_value False
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
            inverted: yes
            """
        When we validate the main config
        And we instantiate MqttIo
        And we initialise GPIO modules
        And we initialise digital inputs
        # Mock this to stop the digital_input_poller from firing events too
        And we mock _handle_digital_input_value on MqttIo
        And we mock _mqtt_publish on MqttIo
        And we fire a new DigitalInputChangedEvent event with
            """
            input_name: mock0
            from_value: true
            to_value: false
            """
        Then _mqtt_publish on MqttIo should be called with MQTT message
            """
            payload: "ON"
            """
