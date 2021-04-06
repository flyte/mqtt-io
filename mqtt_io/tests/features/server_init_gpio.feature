Feature: Tests for the successful initialisation of the GPIO aspects of the server
    Scenario: Successful initialisation of mock GPIO module
        Given a valid config
        And the config has an entry in gpio_modules with
            """
            name: mock
            module: mock
            test: true
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
        Then GPIO module mock should be initialised
        And GPIO module mock should have 1 call(s) to setup_module
        And GPIO config mock should contain
            """
            test: true
            """

    Scenario: Initialising a polled digital input
        Given a valid config
        And the config has an entry in gpio_modules with
            """
            name: mock
            module: mock
            test: true
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
        Then publish_callback function should be subscribed to DigitalInputChangedEvent
        And digital input config mock0 should exist
        And GPIO module mock should have a pin config for mock0
        And GPIO module mock should have a setup_pin() call for mock0
        And mock0 pin should have been set up as an input
        And GPIO module mock shouldn't have a setup_interrupt() call for mock0
        And mock0 shouldn't be configured as a remote interrupt
        And a digital input poller task is added for mock0
        And GPIO module mock shouldn't have an output queue initialised
        And a digital output loop task isn't added for GPIO module mock

    Scenario: Initialising an interrupt digital input
        Given a valid config
        And the config has an entry in gpio_modules with
            """
            name: mock
            module: mock
            test: true
            """
        And the config has an entry in digital_inputs with
            """
            name: mock0
            module: mock
            pin: 0
            interrupt: rising
            """
        When we validate the main config
        And we instantiate MqttIo
        And we initialise GPIO modules
        And we initialise digital inputs
        Then publish_callback function should be subscribed to DigitalInputChangedEvent
        And digital input config mock0 should exist
        And GPIO module mock should have a pin config for mock0
        And GPIO module mock should have a setup_pin() call for mock0
        And mock0 pin should have been set up as an input
        And GPIO module mock should have a setup_interrupt_callback() call for mock0
        And mock0 shouldn't be configured as a remote interrupt
        And mock0 should be configured as a rising interrupt
        And a digital input poller task isn't added for mock0
        And GPIO module mock shouldn't have an output queue initialised
        And a digital output loop task isn't added for GPIO module mock

    Scenario: Initialising an interrupt digital input for another pin
        Given a valid config
        And the config has an entry in gpio_modules with
            """
            name: mock
            module: mock
            test: true
            """
        And the config has an entry in digital_inputs with
            """
            name: mock0
            module: mock
            pin: 0
            interrupt: rising
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
        Then publish_callback function should be subscribed to DigitalInputChangedEvent
        And digital input config mock0 should exist
        And digital input config mock1 should exist
        And GPIO module mock should have a pin config for mock0
        And GPIO module mock should have a pin config for mock1
        And GPIO module mock should have a setup_pin() call for mock0
        And GPIO module mock should have a setup_pin() call for mock1
        And mock0 pin should have been set up as an input
        And mock1 pin should have been set up as an input
        And GPIO module mock should have a setup_interrupt_callback() call for mock0
        And GPIO module mock should have a setup_interrupt_callback() call for mock1
        And mock0 shouldn't be configured as a remote interrupt
        And mock1 should be configured as a remote interrupt
        And mock0 should be configured as a rising interrupt
        And mock1 should be configured as a falling interrupt
        And a digital input poller task isn't added for mock0
        And a digital input poller task is added for mock1
        And GPIO module mock shouldn't have an output queue initialised
        And a digital output loop task isn't added for GPIO module mock

    Scenario: Initialising a digital output
        Given a valid config
        And the config has an entry in gpio_modules with
            """
            name: mock
            module: mock
            test: true
            """
        And the config has an entry in digital_outputs with
            """
            name: mock0
            module: mock
            pin: 0
            """
        When we validate the main config
        And we instantiate MqttIo
        And we initialise GPIO modules
        And we initialise digital outputs
        Then publish_callback function should be subscribed to DigitalOutputChangedEvent
        And digital output config mock0 should exist
        And GPIO module mock should have a pin config for mock0
        And GPIO module mock should have a setup_pin() call for mock0
        And mock0 pin should have been set up as an output
        And GPIO module mock should have an output queue initialised
        And a digital input poller task isn't added for mock0
        And a digital output loop task is added for GPIO module mock

    Scenario: Digital output publishes initial high/on value when publish_initial=True
        Given a valid config
        And the config has an entry in gpio_modules with
            """
            name: mock
            module: mock
            test: true
            """
        And the config has an entry in digital_outputs with
            """
            name: mock0
            module: mock
            pin: 0
            initial: high
            publish_initial: true
            """
        When we validate the main config
        And we instantiate MqttIo
        And we initialise GPIO modules
        And we mock _mqtt_publish on MqttIo
        And we initialise digital outputs
        And we run async tasks
        Then _mqtt_publish on MqttIo should be called with MQTT message
            """
            payload: "ON"
            """

    Scenario: Digital output publishes initial low/off value when publish_initial=True
        Given a valid config
        And the config has an entry in gpio_modules with
            """
            name: mock
            module: mock
            test: true
            """
        And the config has an entry in digital_outputs with
            """
            name: mock0
            module: mock
            pin: 0
            initial: low
            publish_initial: true
            """
        When we validate the main config
        And we instantiate MqttIo
        And we initialise GPIO modules
        And we mock _mqtt_publish on MqttIo
        And we initialise digital outputs
        And we run async tasks
        Then _mqtt_publish on MqttIo should be called with MQTT message
            """
            payload: "OFF"
            """


    Scenario: Inverted digital output publishes initial high/off value when publish_initial=True
        Given a valid config
        And the config has an entry in gpio_modules with
            """
            name: mock
            module: mock
            test: true
            """
        And the config has an entry in digital_outputs with
            """
            name: mock0
            module: mock
            pin: 0
            initial: high
            publish_initial: true
            inverted: true
            """
        When we validate the main config
        And we instantiate MqttIo
        And we initialise GPIO modules
        And we mock _mqtt_publish on MqttIo
        And we initialise digital outputs
        And we run async tasks
        Then _mqtt_publish on MqttIo should be called with MQTT message
            """
            payload: "OFF"
            """
    
    Scenario: Inverted digital output publishes initial low/on value when publish_initial=True
        Given a valid config
        And the config has an entry in gpio_modules with
            """
            name: mock
            module: mock
            test: true
            """
        And the config has an entry in digital_outputs with
            """
            name: mock0
            module: mock
            pin: 0
            initial: low
            publish_initial: true
            inverted: true
            """
        When we validate the main config
        And we instantiate MqttIo
        And we initialise GPIO modules
        And we mock _mqtt_publish on MqttIo
        And we initialise digital outputs
        And we run async tasks
        Then _mqtt_publish on MqttIo should be called with MQTT message
            """
            payload: "ON"
            """

    Scenario: Digital output publishes ON when turned on
        Given a valid config
        And the config has an entry in gpio_modules with
            """
            name: mock
            module: mock
            test: true
            """
        And the config has an entry in digital_outputs with
            """
            name: mock0
            module: mock
            pin: 0
            """
        When we validate the main config
        And we instantiate MqttIo
        And we initialise GPIO modules
        And we mock _mqtt_publish on MqttIo
        And we initialise digital outputs
        And we set digital output mock0 to on
        And we run async tasks
        Then _mqtt_publish on MqttIo should be called with MQTT message
            """
            payload: "ON"
            """
    
    Scenario: Digital output publishes OFF when turned off
        Given a valid config
        And the config has an entry in gpio_modules with
            """
            name: mock
            module: mock
            test: true
            """
        And the config has an entry in digital_outputs with
            """
            name: mock0
            module: mock
            pin: 0
            """
        When we validate the main config
        And we instantiate MqttIo
        And we initialise GPIO modules
        And we mock _mqtt_publish on MqttIo
        And we initialise digital outputs
        And we set digital output mock0 to off
        And we run async tasks
        Then _mqtt_publish on MqttIo should be called with MQTT message
            """
            payload: "OFF"
            """

    Scenario: Inverted digital output publishes ON when turned on
        Given a valid config
        And the config has an entry in gpio_modules with
            """
            name: mock
            module: mock
            test: true
            """
        And the config has an entry in digital_outputs with
            """
            name: mock0
            module: mock
            pin: 0
            inverted: true
            """
        When we validate the main config
        And we instantiate MqttIo
        And we initialise GPIO modules
        And we mock _mqtt_publish on MqttIo
        And we initialise digital outputs
        And we set digital output mock0 to on
        And we run async tasks
        Then _mqtt_publish on MqttIo should be called with MQTT message
            """
            payload: "ON"
            """
    
    Scenario: Inverted digital output publishes OFF when turned off
        Given a valid config
        And the config has an entry in gpio_modules with
            """
            name: mock
            module: mock
            test: true
            """
        And the config has an entry in digital_outputs with
            """
            name: mock0
            module: mock
            pin: 0
            inverted: true
            """
        When we validate the main config
        And we instantiate MqttIo
        And we initialise GPIO modules
        And we mock _mqtt_publish on MqttIo
        And we initialise digital outputs
        And we set digital output mock0 to off
        And we run async tasks
        Then _mqtt_publish on MqttIo should be called with MQTT message
            """
            payload: "OFF"
            """