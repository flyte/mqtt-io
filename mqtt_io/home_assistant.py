"""
Home Assistant MQTT Discovery features.

https://www.home-assistant.io/docs/mqtt/discovery/
"""

import json
import logging
from typing import Any, Dict

from .constants import INPUT_TOPIC, OUTPUT_TOPIC, SENSOR_TOPIC, SET_SUFFIX
from .mqtt import MQTTClientOptions, MQTTMessageSend
from .types import ConfigType
from . import VERSION

_LOG = logging.getLogger(__name__)


def get_common_config(
    io_conf: ConfigType, mqtt_conf: ConfigType, mqtt_options: MQTTClientOptions
) -> Dict[str, Any]:
    """
    Return config that's common across all HQ discovery announcements.
    """
    disco_conf: ConfigType = mqtt_conf["ha_discovery"]
    config = {"name": io_conf['name']}
    config.update(
        {
            "availability_topic": '/'.join(
                (mqtt_conf["topic_prefix"], mqtt_conf["status_topic"])
            ),
            "payload_available": mqtt_conf["status_payload_running"],
            "payload_not_available": mqtt_conf["status_payload_dead"],
            "device": {
                "manufacturer": 'MQTT IO',
                "model": f'v{VERSION}',
                "identifiers": [mqtt_options.client_id],
                "name": disco_conf["name"],
            },
        }
    )
    config.update(io_conf.get("ha_discovery", {}))
    return config


def hass_announce_digital_input(
    in_conf: ConfigType, mqtt_conf: ConfigType, mqtt_options: MQTTClientOptions
) -> MQTTMessageSend:
    """
    Create a message which announces digital input as binary_sensor to Home Assistant.
    """
    disco_conf: ConfigType = mqtt_conf["ha_discovery"]
    name: str = in_conf["name"]
    disco_prefix: str = disco_conf["prefix"]
    sensor_config = get_common_config(in_conf, mqtt_conf, mqtt_options)
    sensor_config.update(
        {
            "unique_id": f'{mqtt_options.client_id}_{in_conf["module"]}_input_{name}',
            "state_topic": '/'.join((mqtt_conf["topic_prefix"], INPUT_TOPIC, name)),
            "payload_on": in_conf["on_payload"],
            "payload_off": in_conf["off_payload"],
        }
    )
    return MQTTMessageSend(
        "/".join(
            (
                disco_prefix,
                sensor_config.pop("component", "binary_sensor"),
                mqtt_options.client_id,
                name,
                "config",
            )
        ),
        json.dumps(sensor_config).encode("utf8"),
        retain=True,
    )


def hass_announce_digital_output(
    out_conf: ConfigType,
    mqtt_conf: ConfigType,
    mqtt_options: MQTTClientOptions,
) -> MQTTMessageSend:
    """
    Create a message which announces digital output as switch to Home Assistant.
    """
    disco_conf: ConfigType = mqtt_conf["ha_discovery"]
    name: str = out_conf["name"]
    prefix: str = mqtt_conf["topic_prefix"]
    disco_prefix: str = disco_conf["prefix"]
    switch_config = get_common_config(out_conf, mqtt_conf, mqtt_options)
    switch_config.update(
        {
            "unique_id": f'{mqtt_options.client_id}_{out_conf["module"]}_output_{name}',
            "state_topic": '/'.join((prefix, OUTPUT_TOPIC, name)),
            "command_topic": '/'.join((prefix, OUTPUT_TOPIC, name, SET_SUFFIX)),
            "payload_on": out_conf["on_payload"],
            "payload_off": out_conf["off_payload"],
        }
    )
    return MQTTMessageSend(
        "/".join(
            (
                disco_prefix,
                switch_config.pop("component", "switch"),
                mqtt_options.client_id,
                name,
                "config",
            )
        ),
        json.dumps(switch_config).encode("utf8"),
        retain=True,
    )


def hass_announce_sensor_input(
    sens_conf: ConfigType,
    mqtt_conf: ConfigType,
    mqtt_options: MQTTClientOptions,
) -> MQTTMessageSend:
    """
    Create a message which announces digital output as sensor to Home Assistant.
    """
    disco_conf: ConfigType = mqtt_conf["ha_discovery"]
    name: str = sens_conf["name"]
    prefix: str = mqtt_conf["topic_prefix"]
    disco_prefix: str = disco_conf["prefix"]
    sensor_config = get_common_config(sens_conf, mqtt_conf, mqtt_options)
    sensor_config.update(
        {
            "unique_id": f'{mqtt_options.client_id}_{sens_conf["module"]}_sensor_{name}',
            "state_topic": '/'.join((prefix, SENSOR_TOPIC, name)),
        }
    )
    if "expire_after" not in sensor_config:
        sensor_config["expire_after"] = sens_conf["interval"] * 2 + 5

    return MQTTMessageSend(
        "/".join(
            (
                disco_prefix,
                sensor_config.pop("component", "sensor"),
                mqtt_options.client_id,
                name,
                "config",
            )
        ),
        json.dumps(sensor_config).encode("utf8"),
        retain=True,
    )
