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

_LOG = logging.getLogger(__name__)


def get_common_config(
    mqtt_config: ConfigType, mqtt_options: MQTTClientOptions
) -> Dict[str, Any]:
    """
    Return config that's common across all HQ discovery announcements.
    """
    return dict(
        availability_topic="/".join(
            (mqtt_config["topic_prefix"], mqtt_config["status_topic"])
        ),
        payload_available=mqtt_config["status_payload_running"],
        payload_not_available=mqtt_config["status_payload_dead"],
        device=dict(
            manufacturer="MQTT IO",
            identifiers=["mqtt-io", mqtt_options.client_id],
            name=mqtt_config["discovery_name"],
        ),
    )


def hass_announce_digital_input(
    in_conf: ConfigType, mqtt_config: ConfigType, mqtt_options: MQTTClientOptions
) -> MQTTMessageSend:
    """
    Create a message which announces digital input as binary_sensor to Home Assistant.
    """
    name: str = in_conf["name"]
    disco_prefix: str = mqtt_config["discovery_prefix"]
    sensor_config = get_common_config(mqtt_config, mqtt_options)
    sensor_config.update(
        dict(
            name=name,
            unique_id=f"{mqtt_options.client_id}_{in_conf['module']}_input_{name}",
            state_topic="/".join((mqtt_config["topic_prefix"], INPUT_TOPIC, name)),
            payload_on=in_conf["on_payload"],
            payload_off=in_conf["off_payload"],
        )
    )
    return MQTTMessageSend(
        "/".join((disco_prefix, "binary_sensor", mqtt_options.client_id, name, "config")),
        json.dumps(sensor_config).encode("utf8"),
        retain=True,
    )


def hass_announce_digital_output(
    out_conf: ConfigType,
    mqtt_config: ConfigType,
    mqtt_options: MQTTClientOptions,
) -> MQTTMessageSend:
    """
    Create a message which announces digital output as switch to Home Assistant.
    """
    name: str = out_conf["name"]
    prefix: str = mqtt_config["topic_prefix"]
    disco_prefix: str = mqtt_config["discovery_prefix"]
    switch_config = get_common_config(mqtt_config, mqtt_options)
    switch_config.update(
        dict(
            name=name,
            unique_id=f"{mqtt_options.client_id}_{out_conf['module']}_output_{name}",
            state_topic="/".join((prefix, OUTPUT_TOPIC, name)),
            command_topic="/".join((prefix, OUTPUT_TOPIC, name, SET_SUFFIX)),
            payload_on=out_conf["on_payload"],
            payload_off=out_conf["off_payload"],
        )
    )
    return MQTTMessageSend(
        "/".join((disco_prefix, "switch", mqtt_options.client_id, name, "config")),
        json.dumps(switch_config).encode("utf8"),
        retain=True,
    )


def hass_announce_sensor_input(
    sens_conf: ConfigType,
    mqtt_config: ConfigType,
    mqtt_options: MQTTClientOptions,
) -> MQTTMessageSend:
    """
    Create a message which announces digital output as sensor to Home Assistant.
    """
    name: str = sens_conf["name"]
    prefix: str = mqtt_config["topic_prefix"]
    disco_prefix: str = mqtt_config["discovery_prefix"]
    expire_after: int = sens_conf.get("expire_after", sens_conf["interval"] * 2 + 5)
    sensor_config = get_common_config(mqtt_config, mqtt_options)
    sensor_config.update(
        dict(
            name=name,
            unique_id=f"{mqtt_options.client_id}_{sens_conf['module']}_sensor_{name}",
            state_topic="/".join((prefix, SENSOR_TOPIC, name)),
            expire_after=expire_after,
        )
    )
    if "unit_of_measurement" in sens_conf:
        sensor_config["unit_of_measurement"] = sens_conf["unit_of_measurement"]
    return MQTTMessageSend(
        "/".join((disco_prefix, "sensor", mqtt_options.client_id, name, "config")),
        json.dumps(sensor_config).encode("utf8"),
        retain=True,
    )
