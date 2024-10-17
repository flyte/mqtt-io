Unreleased
==========
- Nothing!

.v2.4.0 - 2024-07-20
====================
- Bump tj-actions/branch-names from 2.2 to 7.0.7 in /.github/workflows by @dependabot in https://github.com/flyte/mqtt-io/pull/339
- # Fix for poetry/docutils related bug by @BenjiU in https://github.com/flyte/mqtt-io/pull/367
- upgrade DHT11/DHT22 backing library by @pansila in https://github.com/flyte/mqtt-io/pull/297
- Install gcc for slim docker to build rpi.gpio on demand by @BenjiU in https://github.com/flyte/mqtt-io/pull/368
- Remove lint warnings from bmp085.py by @BenjiU in https://github.com/flyte/mqtt-io/pull/375
- Add support for YF-S201 flow rate sensor by @linucks in https://github.com/flyte/mqtt-io/pull/370
- Support for ENS160  digital multi-gas sensor with multiple IAQ data (TVOC, eCO2, AQI) by @linucks in https://github.com/flyte/mqtt-io/pull/371
- feat: add MH-Z19 sensor module by @kleest in https://github.com/flyte/mqtt-io/pull/365
- Add Support for Sunxi Linux Boards by @fabys77 in https://github.com/flyte/mqtt-io/pull/100

.v2.3.0 - 2024-03-01
====================
- 324 pinned pyyaml version incompatible with latest cython 300 by @BenjiU in #325
- fix pipeline for tagging by @BenjiU in #323
- pin pyyaml to v6.0.1 by @BenjiU in #326
- Add new module for sensor adxl345 by @birdie1 in #223
- Sensor INA219: Use optional i2c_bus_num by @mschlenstedt in #328
- Update ads1x15.py by @maxthebuch in #329
- repeat subscribe when reconnected to MQTT broker by @JohannesHennecke in #337
- Fix non-unique identifiers reporting to HA by @dolai1 in #345
- docker: use a "slim" base image by @chatziko in #342
- Fix applying mqtt.reconnect_count by reordering except clauses by @zzeekk in #331
- Add PMS5003 Particulate Sensor by @johnwang16 in #346
- gpiod: enable pullup/pulldown by @chatziko in #341
- docker: slim image, use rustup, build deps only on armv7 by @chatziko in #352

.v2.2.9d - 2023-07-18
====================
- new sensors
- fix for reconnection problem

.v2.2.8 - 2023-01-19
====================
- Fix for #280 by @rlehfeld in #281
- Fix reconnects_remaining referenced before assignment by @SamLeatherdale in #274
- Only create one instance of sensor_module for ADS1x15 by @shbatm in #286
- PN532 NFC/RFID reader implementation by @vytautassurvila in #269
- Update README.md by @OzGav in #264
- FIX OrangePi module by @neatherweb in #285
- New DockerPi 4 Channel Relay GPIO module by @claudegel in #246
- Digital Output: fix initial state inconsistency by @hacker-cb in #238
- Add module mcp3xxx by @koleo9am in #227
- Always remove finished transient_tasks. by @gmsoft-tuxicoman in #301

.v2.2.7 - 2022-07-07
====================
- Fix some minor pylint issues and silence some others.
- Fix bug with changing reference to 'edge' in raspberrypi module. #268 @vytautassurvila
- Add INA219 sensor module. #221 @birdie1
- Implement PinPUD.OFF for pcf8574/5. #217 @IlmLV
- Ensure HCSR04 distance cannot be None. #215 @joseffallman
- Add GPIOZero module. #212 @fipwmaqzufheoxq92ebc
- Render config with confp to allow dynamic configuration based on environment/redis/etcd vars. #210 @fipwmaqzufheoxq92ebc
- Log uncaught exceptions to configured logging handlers. #206 @fipwmaqzufheoxq92ebc

v2.2.6 - 2021-04-23
===================
- Create docs in a tempdir to stop them from being clobbered when changing branches.

v2.2.5 - 2021-04-23
===================
- Sort versions in docs. Use git pull properly.

v2.2.4 - 2021-04-23
===================
- Generate docs versions and root index to strings and write them after switching branches

v2.2.3 - 2021-04-23
===================
- Add docs root index to git separately

v2.2.2 - 2021-04-23
===================
- Fix version regex for docs index generation

v2.2.1 - 2021-04-23
===================
- Handle tags in generate docs script.

v2.2.0 - 2021-04-23
===================
- Multi-versioned documentation.
- Auto-reconnect to MQTT server on disconnection. #207 @fipwmaqzufheoxq92ebc

v2.1.8 - 2021-04-21
===================
- Fix broken hcsr04 sensor that I (@flyte) broke when rewriting for v2.x. #211 @r00tat
- Fix inversion not taken into account when publishing initial digital output value. #203 @r00tat
- Fix #198 where Future wasn't created from the right thread. #205 @fipwmaqzufheoxq92ebc

v2.1.7 - 2021-04-01
===================
- Add install_requirements config option to skip installing missing module requirements. #199

v2.1.6 - 2021-04-01
===================
- Add ADS1x15 module. #200 @r00tat

v2.1.5 - 2021-04-01
===================
- Update PyYAML version to 5.4 CVE-2020-14343

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
