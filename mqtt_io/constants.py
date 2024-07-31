"""
Constant values used in MQTT IO.
"""

SET_SUFFIX = "set"
SET_ON_MS_SUFFIX = "set_on_ms"
SET_OFF_MS_SUFFIX = "set_off_ms"
SEND_SUFFIX = "send"

INPUT_TOPIC = "input"
OUTPUT_TOPIC = "output"
SENSOR_TOPIC = "sensor"
STREAM_TOPIC = "stream"

MODULE_IMPORT_PATH = "mqtt_io.modules"
MODULE_CLASS_NAMES = {"gpio": 'GPIO', "sensor": 'Sensor', "stream": 'Stream'}

MQTT_SUB_PRIORITY = 1
MQTT_ANNOUNCE_PRIORITY = 2
MQTT_PUB_PRIORITY = 3
