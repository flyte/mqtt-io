Feature: Valid main config validation

    # MQTT

    Scenario: MQTT section with host should pass
        Given a valid config
        When we validate the main config
        Then the config validates
    
    # GPIO

    Scenario: GPIO module with digital_input and digital_output should validate
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
            """
        When we validate the main config
        Then the config validates

    Scenario: The same pin number used across different modules should validate
        Given a valid config
        Given the config has an entry in gpio_modules with
            """
            name: mockA
            module: mock
            """
        Given the config has an entry in gpio_modules with
            """
            name: mockB
            module: mock
            """
        And the config has an entry in digital_inputs with
            """
            name: mock0A
            module: mockA
            pin: 0
            """
        And the config has an entry in digital_inputs with
            """
            name: mock0B
            module: mockB
            pin: 0
            """
        When we validate the main config
        Then the config validates

    Scenario Outline: A GPIO module with a single config in <section> should validate
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
        When we validate the main config
        Then the config validates
    
        Examples:
            | section |
            | digital_inputs |
            | digital_outputs |

