"""
Home Assistant MQTT Discovery features.

https://www.home-assistant.io/docs/mqtt/discovery/
"""

import json
import logging
from typing import TYPE_CHECKING

from .constants import INPUT_TOPIC, OUTPUT_TOPIC, SENSOR_TOPIC, SET_SUFFIX
from .types import ConfigType

if TYPE_CHECKING:
    from hbmqtt.client import MQTTClient  # type: ignore

_LOG = logging.getLogger(__name__)


async def hass_announce_digital_input(
    in_conf: ConfigType, mqtt_config: ConfigType, mqtt_client: "MQTTClient"
) -> None:
    """
    Announces digital input as binary_sensor to HomeAssistant.
    :param in_conf: Input config
    :type in_conf: dict
    :return: None
    :rtype: NoneType
    """
    sensor_name = in_conf["name"]
    sensor_config = {
        "name": sensor_name,
        "unique_id": "%s_%s_input_%s"
        % (mqtt_client.client_id, in_conf["module"], sensor_name),
        "state_topic": "%s/%s/%s"
        % (mqtt_config["topic_prefix"], INPUT_TOPIC, in_conf["name"]),
        "availability_topic": "%s/%s"
        % (mqtt_config["topic_prefix"], mqtt_config["status_topic"]),
        "payload_available": mqtt_config["status_payload_running"],
        "payload_not_available": mqtt_config["status_payload_dead"],
        "payload_on": in_conf["on_payload"],
        "payload_off": in_conf["off_payload"],
        "device": {
            "manufacturer": "MQTT IO",
            "identifiers": ["mqtt-io", mqtt_client.client_id],
            "name": mqtt_config["discovery_name"],
        },
    }

    _LOG.info(
        "Sending Home Assistant discovery message for digital input '%s'", in_conf["name"]
    )
    await mqtt_client.publish(
        "%s/%s/%s/%s/config"
        % (
            mqtt_config["discovery_prefix"],
            "binary_sensor",
            mqtt_client.client_id,
            sensor_name,
        ),
        json.dumps(sensor_config).encode("utf8"),
        retain=True,
    )


async def hass_announce_digital_output(
    out_conf: ConfigType, mqtt_config: ConfigType, mqtt_client: "MQTTClient"
) -> None:
    """
    Announces digital output as switch to HomeAssistant.
    :param out_conf: Output config
    :type out_conf: dict
    :return: None
    :rtype: NoneType
    """
    switch_name = out_conf["name"]
    switch_config = {
        "name": switch_name,
        "unique_id": "%s_%s_output_%s"
        % (mqtt_client.client_id, out_conf["module"], switch_name),
        "state_topic": "%s/%s/%s"
        % (mqtt_config["topic_prefix"], OUTPUT_TOPIC, out_conf["name"]),
        "command_topic": "%s/%s/%s/%s"
        % (mqtt_config["topic_prefix"], OUTPUT_TOPIC, out_conf["name"], SET_SUFFIX),
        "availability_topic": "%s/%s"
        % (mqtt_config["topic_prefix"], mqtt_config["status_topic"]),
        "payload_available": mqtt_config["status_payload_running"],
        "payload_not_available": mqtt_config["status_payload_dead"],
        "payload_on": out_conf["on_payload"],
        "payload_off": out_conf["off_payload"],
        "device": {
            "manufacturer": "MQTT IO",
            "identifiers": ["mqtt-io", mqtt_client.client_id],
            "name": mqtt_config["discovery_name"],
        },
    }

    _LOG.info(
        "Sending Home Assistant discovery message for digital output '%s'",
        out_conf["name"],
    )
    await mqtt_client.publish(
        "%s/%s/%s/%s/config"
        % (
            mqtt_config["discovery_prefix"],
            "switch",
            mqtt_client.client_id,
            switch_name,
        ),
        json.dumps(switch_config).encode("utf8"),
        retain=True,
    )


async def hass_announce_sensor_input(
    sens_conf: ConfigType, mqtt_config: ConfigType, mqtt_client: "MQTTClient"
) -> None:
    """
    Announces digital output as sensor to HomeAssistant.
    :param sens_conf: Sensor config
    :type sens_conf: dict
    :return: None
    :rtype: NoneType
    """
    sensor_name = sens_conf["name"]
    sensor_config = {
        "name": sensor_name,
        "unique_id": "%s_%s_output_%s"
        % (mqtt_client.client_id, sens_conf["module"], sensor_name),
        "state_topic": "%s/%s/%s"
        % (mqtt_config["topic_prefix"], SENSOR_TOPIC, sens_conf["name"]),
        "availability_topic": "%s/%s"
        % (mqtt_config["topic_prefix"], mqtt_config["status_topic"]),
        "payload_available": mqtt_config["status_payload_running"],
        "payload_not_available": mqtt_config["status_payload_dead"],
        "expire_after": 2 * int(sens_conf.get("interval", "60")) + 5,
        "device": {
            "manufacturer": "MQTT IO",
            "identifiers": ["mqtt-io", mqtt_client.client_id],
            "name": mqtt_config["discovery_name"],
        },
    }
    if "unit_of_measurement" in sens_conf:
        sensor_config["unit_of_measurement"] = sens_conf["unit_of_measurement"]

    _LOG.info(
        "Sending Home Assistant discovery message for sensor '%s'",
        sens_conf["name"],
    )
    await mqtt_client.publish(
        "%s/%s/%s/%s/config"
        % (
            mqtt_config["discovery_prefix"],
            "sensor",
            mqtt_client.client_id,
            sensor_name,
        ),
        json.dumps(sensor_config).encode("utf8"),
        retain=True,
    )
