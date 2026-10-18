# Config Schema

The software is configured using a single YAML file specified as the first argument upon execution.

In order to help avoid any misconfigurations, the provided configuration file is tested against a [Cerberus](https://docs.python-cerberus.org/en/stable/) schema and the program will display errors and exit during its initialisation phase if errors are found. Failing fast is preferable to only failing when, for example, an MQTT is received and the software attempts to control a module accordingly. This enables the user to fix the config while it's still fresh in mind, instead of some arbitrary amount of time down the line when the software may no longer be being supervised.

The main configuration schema is laid out in `mqtt_io/config/config.schema.yml` and further schema may be optionally set as part of each module in the `CONFIG_SCHEMA` constant. This behaviour allows the modules to optionally require extra configuration specific to them.

Sensor and stream modules may also specify a config schema to be applied to each of the configured sensors and streams within the `sensor_inputs`, `stream_reads` and `stream_writes` sections.