Feature: Invalid main config validation

    # MQTT

    Scenario: Missing MQTT section should fail
        # Just add the gpio_modules section without the mqtt one
        Given the config has an entry in gpio_modules with
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
        Then config validation fails

    Scenario: Missing MQTT host should fail
        # Just add the mqtt section without host
        Given the config has an mqtt section
        When we validate the main config
        Then config validation fails

    # GPIO

    Scenario: Digital input with no existing module should fail
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
        And the config has an entry in digital_inputs with
            """
            name: mock1
            module: doesntexist
            pin: 1
            """
        When we validate the main config
        Then config validation fails

    Scenario: Digital output with no existing module should fail
        Given a valid config
        And the config has an entry in gpio_modules with
            """
            name: mock
            module: mock
            """
        And the config has an entry in digital_outputs with
            """
            name: mock0
            module: mock
            pin: 0
            """
        And the config has an entry in digital_outputs with
            """
            name: mock1
            module: doesntexist
            pin: 1
            """
        When we validate the main config
        Then config validation fails

    Scenario: Two GPIO modules with the same name should fail
        Given a valid config
        And the config has an entry in gpio_modules with
            """
            name: mock
            module: mock
            """
        And the config has an entry in gpio_modules with
            """
            name: mock
            module: mock
            """
        When we validate the main config
        Then config validation fails

    Scenario: GPIO modules without digital_inputs or digital_outputs should fail
        Given a valid config
        And the config has an entry in gpio_modules with
            """
            name: mock
            module: mock
            """
        When we validate the main config
        Then config validation fails

    @skip
    Scenario: Configuring a GPIO module's pin as a digital input twice should fail
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
        And the config has an entry in digital_inputs with
            """
            name: mock1
            module: mock
            pin: 0
            """
        When we validate the main config
        Then config validation fails

    @skip
    Scenario: Configuring a GPIO module's pin as a digital output twice should fail
        Given a valid config
        And the config has an entry in gpio_modules with
            """
            name: mock
            module: mock
            """
        And the config has an entry in digital_outputs with
            """
            name: mock0
            module: mock
            pin: 0
            """
        And the config has an entry in digital_outputs with
            """
            name: mock1
            module: mock
            pin: 0
            """
        When we validate the main config
        Then config validation fails

    @skip
    Scenario: Configuring a GPIO module's pin as a digital output and a digital input should fail
        Given a valid config
        And the config has an entry in gpio_modules with
            """
            name: mock
            module: mock
            """
        And the config has an entry in digital_outputs with
            """
            name: mock0
            module: mock
            pin: 0
            """
        And the config has an entry in digital_inputs with
            """
            name: mock1
            module: mock
            pin: 0
            """
        When we validate the main config
        Then config validation fails

    Scenario Outline: Using the same name for two <section> should not validate
        Given a valid config
        Given the config has an entry in gpio_modules with
            """
            name: mock
            module: mock
            """
        And the config has an entry in <section> with
            """
            name: mock0
            module: mock
            pin: 0
            """
        And the config has an entry in <section> with
            """
            name: mock0
            module: mock
            pin: 1
            """
        When we validate the main config
        Then config validation fails

        Examples:
            | section |
            | digital_inputs |
            | digital_outputs |

    Scenario: Using a pin that's not configured as an interrupt in an interrupt_for list should not validate
        Given a valid config
        Given the config has an entry in gpio_modules with
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
        And the config has an entry in digital_inputs with
            """
            name: mock1
            module: mock
            pin: 1
            interrupt: rising
            interrupt_for:
            - mock0
            """
        When we validate the main config
        Then config validation fails

    Scenario: Configuring a pin as an interrupt_for another pin without making it an interrupt itself should not validate
        Given a valid config
        Given the config has an entry in gpio_modules with
            """
            name: mock
            module: mock
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
            interrupt_for:
            - mock0
            """
        When we validate the main config
        Then config validation fails

    Scenario: Configuring a pin as an interrupt_for itself should not validate
        Given a valid config
        Given the config has an entry in gpio_modules with
            """
            name: mock
            module: mock
            """
        And the config has an entry in digital_inputs with
            """
            name: mock1
            module: mock
            pin: 1
            interrupt_for:
            - mock1
            """
        When we validate the main config
        Then config validation fails

