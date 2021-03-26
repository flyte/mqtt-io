v2.1.4 - 2021-03-26
===================
- Add version to 'model' field of HA Discovery config payload. #196 @pbill2003

v2.1.3 - 2021-03-26
===================
- Add missing `spi_device` config schema entry for MCP3008 sensor module. #194

v2.1.2 - 2021-03-24
===================
- Remove config validation that checks usage of the same numbered pin used twice. #191

v2.1.1 - 2021-03-16
===================
- Fix bodged BH1750 sensor value reading code. #189

v2.1.0 - 2021-03-11
===================
- Add *OPT-IN* error reporting to sentry. Bumps minor version because it adds a config entry.

v2.0.1 - 2021-03-11
===================
- Fix bug where sensor config was retrieved from the wrong place https://github.com/flyte/mqtt-io/issues/185

v2.0.0 - 2021-03-07
===================
- Rewrite core with asyncio
- Change MQTT client to asyncio-mqtt
- Add better validation for config
- [Move some config values around](https://flyte.github.io/mqtt-io/#/config/v2-changes), but mostly stay compatible with existing configs
- Add MCP23017 module
- [Rework interrupts](https://flyte.github.io/mqtt-io/#/config/interrupts) to allow for pins to be interrupts for other pins on other modules
- Enable extra values to be added to the [Home Assistant Discovery](https://flyte.github.io/mqtt-io/#/config/ha_discovery) config payloads
- Rename package from pi-mqtt-gpio to mqtt-io since it's not just for Raspberry Pi, and not just for GPIO
- Create generated documentation for the config file options ("Section Reference" section of [the documentation](https://flyte.github.io/mqtt-io/#/))
- Tons more stuff, too varied to list here. It's safe to say that almost everything has been improved (hopefully) in some way

v0.5.3 - 2020-10-17
===================
- Add PCF8575 support. #121
- Add MCP3008 sensor support. #115
- Add AHT20 sensor support. #122
- Add BME280 sensor support. #132
- Install requirements using current Python executable. #134
- Add sensors to HASS discovery. #133
- Add option to publish output value on startup. #125

v0.5.2 - 2020-10-17
===================
- Update PyYAML to a version that doesn't suffer from CVE-2020-1747 vulnerability.
- Add 'stream' IO.

v0.3.1 - 2019-03-10
===================
- Pin safe version of PyYAML in requirements.

v0.3.0 - 2019-03-10
===================
- Merge PR from @BenjiU which implements a new sensor interface. #52

v0.0.12 - 2017-07-26
====================
- Add cleanup function to modules which are called before program exit. #16

v0.0.11 - 2017-07-26
====================
- Decode received MQTT message payload as utf8 before trying to match with on/off payload values. #14

v0.0.10 - 2017-07-26
====================
- Fix bug with selection of pullup value in raspberrypi module when none set. #15

v0.0.9 - 2017-07-26
===================
- Successful fix for bug with loading config schema. #13

v0.0.8 - 2017-07-26
===================
- Failed fix for bug with loading config schema. #13

v0.0.7 - 2017-07-17
===================

- Implement `set_on_ms` and `set_off_ms` topic suffixes. Closes #10

v0.0.6 - 2017-07-17
===================

- Large refactor and tidyup.
- Implement config validation using cerberus.
- Enable configuration of MQTT protocol. Closes #11.
- Deploy Python Wheel as well as source package.
- Add some (not exhaustive) tests.
