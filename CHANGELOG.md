v0.3.1 - 2019-03-10
===================
- Pin safe version of PyYAML in requirements

v0.3.0 - 2019-03-10
===================
- Merge PR from @BenjiU which implements a new sensor interface. #52

---

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
