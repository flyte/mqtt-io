"""
Validation functions for GPIO configs.
"""

from collections import Counter
from typing import Any, Dict, Iterable, List, Set

from ...types import ConfigType
from . import BadConfigsType, add_error


def validate_gpio_module_names(
    bad_configs: BadConfigsType,
    config: ConfigType,
    module_section: str,
    io_sections: Iterable[str],
) -> None:
    """
    Ensure that all of the IO config sections refer to existing module names.
    """
    module_names = {x["name"] for x in config.get(module_section, [])}

    for io_section in io_sections:
        for io_conf in config.get(io_section, []):
            if io_conf["module"] not in module_names:
                add_error(
                    bad_configs,
                    io_section,
                    io_conf["name"],
                    "%s section has no module configured with the name '%s'"
                    % (
                        module_section,
                        io_conf["module"],
                    ),
                )


def validate_gpio_modules_have_io_sections(
    bad_configs: BadConfigsType,
    config: ConfigType,
) -> None:
    """
    Ensure that all GPIO modules have an IO section.
    """
    digital_inputs = config.get("digital_inputs", [])
    digital_outputs = config.get("digital_outputs", [])
    modules_used = set(x["module"] for x in digital_inputs + digital_outputs)

    for module in config.get("gpio_modules", []):
        if module["name"] not in modules_used:
            add_error(
                bad_configs,
                "gpio_modules",
                module["name"],
                "GPIO module '%s' does not have any digital_input or digital_output configs"
                % module["name"],
            )


def validate_gpio_pins_only_configured_once(
    bad_configs: BadConfigsType,
    config: ConfigType,
) -> None:
    """
    Ensure that any GPIO pins are only configured once.
    """
    digital_inputs: List[Dict[str, Any]] = config.get("digital_inputs", [])
    digital_outputs: List[Dict[str, Any]] = config.get("digital_outputs", [])
    io_confs_per_module: Dict[str, List[Dict[str, Any]]] = {}
    for io_conf in digital_inputs + digital_outputs:
        io_confs_per_module.setdefault(io_conf["module"], []).append(io_conf)
    for module_name, io_confs in io_confs_per_module.items():
        pin_config_counts = Counter(io_conf["pin"] for io_conf in io_confs)
        duplicated_pins = [pin for pin, count in pin_config_counts.items() if count > 1]
        for dup_pin in duplicated_pins:
            add_error(
                bad_configs,
                "gpio_modules",
                module_name,
                "Pin '%s' has more than one configuration in digital_inputs or digital_outputs"
                % dup_pin,
            )


def validate_gpio_interrupt_for(
    bad_configs: BadConfigsType,
    digital_inputs: List[ConfigType],
) -> None:
    """
    Ensure that:
    - Pins listed in interrupt_for are configured as interrupts
    - A pin's interrupt_for doesn't contain itself
    - A pin with interrupt_for is configured as an interrupt
    """
    interrupt_pins: Set[str] = set(
        in_conf["name"] for in_conf in digital_inputs if in_conf.get("interrupt")
    )
    for in_conf in [x for x in digital_inputs if x.get("interrupt_for")]:
        errors = []
        if "interrupt" not in in_conf:
            errors.append(
                "Pin is configured as an 'interrupt_for' other pins, but is not "
                "configured as an interrupt itself"
            )
        for pin_name in in_conf["interrupt_for"]:
            if pin_name not in interrupt_pins:
                errors.append(
                    f"Pin '{pin_name}' listed in 'interrupt_for' is not configured as an "
                    "interrupt itself"
                )
            if pin_name == in_conf["name"]:
                errors.append(f"Pin '{pin_name}' lists itself in 'interrupt_for'")

        for error in errors:
            add_error(bad_configs, "digital_inputs", in_conf["name"], error)
