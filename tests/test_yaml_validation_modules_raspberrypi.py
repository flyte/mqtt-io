import pytest

from importlib import import_module
import cerberus
import yaml
import copy

from pi_mqtt_gpio import CONFIG_SCHEMA
from pi_mqtt_gpio.modules import BASE_SCHEMA

gpio_module = import_module("pi_mqtt_gpio.modules.raspberrypi")

# Doesn't need to be a deep copy because we won't modify the base
# validation rules, just add more of them.
module_config_schema_input = CONFIG_SCHEMA.copy()
module_config_schema_input = {"digital_inputs" : module_config_schema_input["digital_inputs"]}
module_config_schema_input.update(
    getattr(gpio_module, "CONFIG_SCHEMA", {}))
#print yaml.dump(module_config_schema_input)
module_validator_input = cerberus.Validator(module_config_schema_input)

module_config_schema_output = CONFIG_SCHEMA.copy()
module_config_schema_output = {"digital_outputs" : module_config_schema_output["digital_outputs"]}
module_config_schema_output.update(
    getattr(gpio_module, "CONFIG_SCHEMA", {}))
#print yaml.dump(module_config_schema_output)
module_validator_output = cerberus.Validator(module_config_schema_output)

digital_inputs = {}
digital_outputs = {}
config = {}
with open("config.example.yml") as f:
    config = yaml.safe_load(f)

class ModuleConfigInvalid(Exception):
    def __init__(self, errors, *args, **kwargs):
        self.errors = errors
        super(ModuleConfigInvalid, self).__init__(*args, **kwargs)


@pytest.fixture(autouse=True)
def test_raspberrypi_setup_teardown():
    # reset the digital_inputs, digital_outputs before each test
    global digital_inputs
    global digital_outputs
    # here we need a deep copy, because modifications from previous test
    # shall not bother the following tests
    config_copy = copy.deepcopy(config) #config.deepcopy()
    digital_inputs = {"digital_inputs" : config_copy["digital_inputs"]}
    digital_outputs = {"digital_outputs" : config_copy["digital_outputs"]}
    
    # A test function will be run at this point
    yield

    # Code that will run after your test, for example:
    print(module_validator_input.errors)
    print(module_validator_output.errors)

"""
Tests for raspberry pi digital digital_inputs
"""
def test_yaml_validation_modules_raspberrypi_digital_input_good():
    # test a valid digital_inputs configuration for digital_inputs
    if not module_validator_input.validate(digital_inputs):
        raise ModuleConfigInvalid(module_validator_input.errors)

def test_yaml_validation_modules_raspberrypi_digital_input_unknown_key():
    # test a valid digital_inputs configuration for digital_inputs
    digital_inputs["digital_inputs"][0]['unknown'] = "key"
    with pytest.raises(ModuleConfigInvalid):
        if not module_validator_input.validate(digital_inputs):
            raise ModuleConfigInvalid(module_validator_input.errors)

def test_yaml_validation_modules_raspberrypi_digital_input_module_missing():
    # setup gpio TEST_RASPBERRYPI_GPIO_SET_GET_OUTPUT as output
    del digital_inputs["digital_inputs"][0]['module']
    with pytest.raises(ModuleConfigInvalid):
        if not module_validator_input.validate(digital_inputs):
            raise ModuleConfigInvalid(module_validator_input.errors)

def test_yaml_validation_modules_raspberrypi_digital_input_module_no_string():
    # setup gpio TEST_RASPBERRYPI_GPIO_SET_GET_OUTPUT as output
    digital_inputs["digital_inputs"][0]['module'] = 21
    with pytest.raises(ModuleConfigInvalid):
        if not module_validator_input.validate(digital_inputs):
            yaml.dump(module_validator_input.errors)
            raise ModuleConfigInvalid(module_validator_input.errors)
        
def test_yaml_validation_modules_raspberrypi_digital_input_name_missing():
    # setup gpio TEST_RASPBERRYPI_GPIO_SET_GET_OUTPUT as output
    del digital_inputs["digital_inputs"][0]['name']
    with pytest.raises(ModuleConfigInvalid):
        if not module_validator_input.validate(digital_inputs):
            yaml.dump(module_validator_input.errors)
            raise ModuleConfigInvalid(module_validator_input.errors)

def test_yaml_validation_modules_raspberrypi_digital_input_name_no_string():
    # setup gpio TEST_RASPBERRYPI_GPIO_SET_GET_OUTPUT as output
    digital_inputs["digital_inputs"][0]['name'] = 3.1415
    with pytest.raises(ModuleConfigInvalid):
        if not module_validator_input.validate(digital_inputs):
            yaml.dump(module_validator_input.errors)
            raise ModuleConfigInvalid(module_validator_input.errors)
        
def test_yaml_validation_modules_raspberrypi_digital_input_pin_missing():
    # setup gpio TEST_RASPBERRYPI_GPIO_SET_GET_OUTPUT as output
    del digital_inputs["digital_inputs"][0]['pin']
    with pytest.raises(ModuleConfigInvalid):
        if not module_validator_input.validate(digital_inputs):
            yaml.dump(module_validator_input.errors)
            raise ModuleConfigInvalid(module_validator_input.errors)

def test_yaml_validation_modules_raspberrypi_digital_input_pin_no_number():
    # setup gpio TEST_RASPBERRYPI_GPIO_SET_GET_OUTPUT as output
    digital_inputs["digital_inputs"][0]['pin'] = "12"
    with pytest.raises(ModuleConfigInvalid):
        if module_validator_input.validate(digital_inputs):
            yaml.dump(module_validator_input.errors)
            raise ModuleConfigInvalid(module_validator_input.errors)

def test_yaml_validation_modules_raspberrypi_digital_input_on_payload_no_string():
    # setup gpio TEST_RASPBERRYPI_GPIO_SET_GET_OUTPUT as output
    digital_inputs["digital_inputs"][0]['on_payload'] = True
    with pytest.raises(ModuleConfigInvalid):
        if not module_validator_input.validate(digital_inputs):
            yaml.dump(module_validator_input.errors)
            raise ModuleConfigInvalid(module_validator_input.errors)

def test_yaml_validation_modules_raspberrypi_digital_input_off_payload_no_string():
    # setup gpio TEST_RASPBERRYPI_GPIO_SET_GET_OUTPUT as output
    digital_inputs["digital_inputs"][0]['off_payload'] = 1
    with pytest.raises(ModuleConfigInvalid):
        if not module_validator_input.validate(digital_inputs):
            yaml.dump(module_validator_input.errors)
            raise ModuleConfigInvalid(module_validator_input.errors)

def test_yaml_validation_modules_raspberrypi_digital_input_pullup_missing():
    # setup gpio TEST_RASPBERRYPI_GPIO_SET_GET_OUTPUT as output
    del digital_inputs["digital_inputs"][0]['pullup']
    if not module_validator_input.validate(digital_inputs):
        yaml.dump(module_validator_input.errors)
        raise ModuleConfigInvalid(module_validator_input.errors)

def test_yaml_validation_modules_raspberrypi_digital_input_pullup_no_boolean():
    # setup gpio TEST_RASPBERRYPI_GPIO_SET_GET_OUTPUT as output
    digital_inputs["digital_inputs"][0]['pullup'] = "off"
    with pytest.raises(ModuleConfigInvalid):
        if not module_validator_input.validate(digital_inputs):
            yaml.dump(module_validator_input.errors)
            raise ModuleConfigInvalid(module_validator_input.errors)

def test_yaml_validation_modules_raspberrypi_digital_input_pulldown_missing():
    # setup gpio TEST_RASPBERRYPI_GPIO_SET_GET_OUTPUT as output
    del digital_inputs["digital_inputs"][0]['pulldown']
    if not module_validator_input.validate(digital_inputs):
        yaml.dump(module_validator_input.errors)
        raise ModuleConfigInvalid(module_validator_input.errors)

def test_yaml_validation_modules_raspberrypi_digital_input_pulldown_no_boolean():
    # setup gpio TEST_RASPBERRYPI_GPIO_SET_GET_OUTPUT as output
    digital_inputs["digital_inputs"][0]['pulldown'] = 1
    with pytest.raises(ModuleConfigInvalid):
        if not module_validator_input.validate(digital_inputs):
            yaml.dump(module_validator_input.errors)
            raise ModuleConfigInvalid(module_validator_input.errors)

def test_yaml_validation_modules_raspberrypi_digital_input_retain_optional():
    # setup gpio TEST_RASPBERRYPI_GPIO_SET_GET_OUTPUT as output
    digital_inputs["digital_inputs"][0]['retain'] = True
    if not module_validator_input.validate(digital_inputs):
        yaml.dump(module_validator_input.errors)
        raise ModuleConfigInvalid(module_validator_input.errors)

def test_yaml_validation_modules_raspberrypi_digital_input_retain_no_boolean():
    # setup gpio TEST_RASPBERRYPI_GPIO_SET_GET_OUTPUT as output
    digital_inputs["digital_inputs"][0]['retain'] = "no"
    with pytest.raises(ModuleConfigInvalid):
        if not module_validator_input.validate(digital_inputs):
            yaml.dump(module_validator_input.errors)
            raise ModuleConfigInvalid(module_validator_input.errors)

def test_yaml_validation_modules_raspberrypi_digital_input_interrupt_empty():
    # setup gpio TEST_RASPBERRYPI_GPIO_SET_GET_OUTPUT as output
    digital_inputs["digital_inputs"][0]['interrupt'] = ""
    digital_inputs["digital_inputs"][1]['interrupt'] = None
    with pytest.raises(ModuleConfigInvalid):
        if not module_validator_input.validate(digital_inputs):
            yaml.dump(module_validator_input.errors)
            raise ModuleConfigInvalid(module_validator_input.errors)

def test_yaml_validation_modules_raspberrypi_digital_input_interrupt_valid_values():
    # setup gpio TEST_RASPBERRYPI_GPIO_SET_GET_OUTPUT as output

    # digital_inputs["digital_inputs"][1]['interrupt'] = "rising" #  thats already in example
    if not module_validator_input.validate(digital_inputs):
        yaml.dump(module_validator_input.errors)
        raise ModuleConfigInvalid(module_validator_input.errors)

    digital_inputs["digital_inputs"][1]['interrupt'] = "falling"
    if not module_validator_input.validate(digital_inputs):
        yaml.dump(module_validator_input.errors)
        raise ModuleConfigInvalid(module_validator_input.errors)

    digital_inputs["digital_inputs"][1]['interrupt'] = "both"
    if not module_validator_input.validate(digital_inputs):
        yaml.dump(module_validator_input.errors)
        raise ModuleConfigInvalid(module_validator_input.errors)
"""
Tests for raspberry pi digital digital_outputs
"""
def test_yaml_validation_modules_raspberrypi_digital_output_good():
    # test a valid digital_outputs configuration for digital_outputs
    if not module_validator_output.validate(digital_outputs):
        yaml.dump(module_validator_output.errors)
        raise ModuleConfigInvalid(module_validator_output.errors)

def test_yaml_validation_modules_raspberrypi_digital_output_module_missing():
    # setup gpio TEST_RASPBERRYPI_GPIO_SET_GET_OUTPUT as output
    del digital_outputs["digital_outputs"][0]['module']
    with pytest.raises(ModuleConfigInvalid):
        if not module_validator_output.validate(digital_outputs):
            yaml.dump(module_validator_output.errors)
            raise ModuleConfigInvalid(module_validator_output.errors)

def test_yaml_validation_modules_raspberrypi_digital_output_module_no_string():
    # setup gpio TEST_RASPBERRYPI_GPIO_SET_GET_OUTPUT as output
    digital_outputs["digital_outputs"][0]['module'] = 21
    with pytest.raises(ModuleConfigInvalid):
        if not module_validator_output.validate(digital_outputs):
            yaml.dump(module_validator_output.errors)
            raise ModuleConfigInvalid(module_validator_output.errors)
        
def test_yaml_validation_modules_raspberrypi_digital_output_name_missing():
    # setup gpio TEST_RASPBERRYPI_GPIO_SET_GET_OUTPUT as output
    del digital_outputs["digital_outputs"][0]['name']
    with pytest.raises(ModuleConfigInvalid):
        if not module_validator_output.validate(digital_outputs):
            yaml.dump(module_validator_output.errors)
            raise ModuleConfigInvalid(module_validator_output.errors)

def test_yaml_validation_modules_raspberrypi_digital_output_name_no_string():
    # setup gpio TEST_RASPBERRYPI_GPIO_SET_GET_OUTPUT as output
    digital_outputs["digital_outputs"][0]['name'] = 3.1415
    with pytest.raises(ModuleConfigInvalid):
        if not module_validator_output.validate(digital_outputs):
            yaml.dump(module_validator_output.errors)
            raise ModuleConfigInvalid(module_validator_output.errors)
        
def test_yaml_validation_modules_raspberrypi_digital_output_pin_missing():
    # setup gpio TEST_RASPBERRYPI_GPIO_SET_GET_OUTPUT as output
    del digital_outputs["digital_outputs"][0]['pin']
    with pytest.raises(ModuleConfigInvalid):
        if not module_validator_output.validate(digital_outputs):
            yaml.dump(module_validator_output.errors)
            raise ModuleConfigInvalid(module_validator_output.errors)

def test_yaml_validation_modules_raspberrypi_digital_output_pin_no_number():
    # setup gpio TEST_RASPBERRYPI_GPIO_SET_GET_OUTPUT as output
    digital_outputs["digital_outputs"][0]['pin'] = "12"
    with pytest.raises(ModuleConfigInvalid):
        if module_validator_output.validate(digital_outputs):
            yaml.dump(module_validator_output.errors)
            raise ModuleConfigInvalid(module_validator_output.errors)

def test_yaml_validation_modules_raspberrypi_digital_output_on_payload_missing():
    # setup gpio TEST_RASPBERRYPI_GPIO_SET_GET_OUTPUT as output
    del digital_outputs["digital_outputs"][0]['on_payload']
    if not module_validator_output.validate(digital_outputs):
        yaml.dump(module_validator_output.errors)
        raise ModuleConfigInvalid(module_validator_output.errors)

def test_yaml_validation_modules_raspberrypi_digital_output_on_payload_no_string():
    # setup gpio TEST_RASPBERRYPI_GPIO_SET_GET_OUTPUT as output
    digital_outputs["digital_outputs"][0]['on_payload'] = True
    with pytest.raises(ModuleConfigInvalid):
        if not module_validator_output.validate(digital_outputs):
            yaml.dump(module_validator_output.errors)
            raise ModuleConfigInvalid(module_validator_output.errors)

def test_yaml_validation_modules_raspberrypi_digital_output_off_payload_missing():
    # setup gpio TEST_RASPBERRYPI_GPIO_SET_GET_OUTPUT as output
    del digital_outputs["digital_outputs"][0]['off_payload']
    if not module_validator_output.validate(digital_outputs):
        yaml.dump(module_validator_output.errors)
        raise ModuleConfigInvalid(module_validator_output.errors)

def test_yaml_validation_modules_raspberrypi_digital_output_off_payload_no_string():
    # setup gpio TEST_RASPBERRYPI_GPIO_SET_GET_OUTPUT as output
    digital_outputs["digital_outputs"][0]['off_payload'] = 1
    with pytest.raises(ModuleConfigInvalid):
        if not module_validator_output.validate(digital_outputs):
            yaml.dump(module_validator_output.errors)
            raise ModuleConfigInvalid(module_validator_output.errors)

def test_yaml_validation_modules_raspberrypi_digital_output_inverted_optional():
    # setup gpio TEST_RASPBERRYPI_GPIO_SET_GET_OUTPUT as output
    digital_outputs["digital_outputs"][0]['inverted'] = True
    if not module_validator_output.validate(digital_outputs):
        yaml.dump(module_validator_output.errors)
        raise ModuleConfigInvalid(module_validator_output.errors)

def test_yaml_validation_modules_raspberrypi_digital_output_inverted_no_boolean():
    # setup gpio TEST_RASPBERRYPI_GPIO_SET_GET_OUTPUT as output
    digital_outputs["digital_outputs"][0]['inverted'] = "off"
    with pytest.raises(ModuleConfigInvalid):
        if not module_validator_output.validate(digital_outputs):
            yaml.dump(module_validator_output.errors)
            raise ModuleConfigInvalid(module_validator_output.errors)

def test_yaml_validation_modules_raspberrypi_digital_output_initial_optional_low():
    # setup gpio TEST_RASPBERRYPI_GPIO_SET_GET_OUTPUT as output
    digital_outputs["digital_outputs"][0]['initial'] = "low"
    if not module_validator_output.validate(digital_outputs):
        yaml.dump(module_validator_output.errors)
        raise ModuleConfigInvalid(module_validator_output.errors)

def test_yaml_validation_modules_raspberrypi_digital_output_initial_optional_high():
    # setup gpio TEST_RASPBERRYPI_GPIO_SET_GET_OUTPUT as output
    digital_outputs["digital_outputs"][0]['initial'] = "high"
    if not module_validator_output.validate(digital_outputs):
        yaml.dump(module_validator_output.errors)
        raise ModuleConfigInvalid(module_validator_output.errors)

def test_yaml_validation_modules_raspberrypi_digital_output_initial_no_string():
    # setup gpio TEST_RASPBERRYPI_GPIO_SET_GET_OUTPUT as output
    digital_outputs["digital_outputs"][0]['initial'] = 1
    with pytest.raises(ModuleConfigInvalid):
        if not module_validator_output.validate(digital_outputs):
            yaml.dump(module_validator_output.errors)
            raise ModuleConfigInvalid(module_validator_output.errors)

def test_yaml_validation_modules_raspberrypi_digital_output_retain_optional():
    # setup gpio TEST_RASPBERRYPI_GPIO_SET_GET_OUTPUT as output
    digital_outputs["digital_outputs"][0]['retain'] = True
    if not module_validator_output.validate(digital_outputs):
        yaml.dump(module_validator_output.errors)
        raise ModuleConfigInvalid(module_validator_output.errors)

def test_yaml_validation_modules_raspberrypi_digital_output_retain_no_boolean():
    # setup gpio TEST_RASPBERRYPI_GPIO_SET_GET_OUTPUT as output
    digital_outputs["digital_outputs"][0]['retain'] = "no"
    with pytest.raises(ModuleConfigInvalid):
        if not module_validator_output.validate(digital_outputs):
            yaml.dump(module_validator_output.errors)
            raise ModuleConfigInvalid(module_validator_output.errors)
