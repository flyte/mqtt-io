# Home Assistant Discovery

In order to avoid having to configure your devices both on MQTT IO and on Home Assistant, MQTT IO will [send an announcement](https://www.home-assistant.io/docs/mqtt/discovery/) to Home Assistant to notify it of the devices that have been exposed.

## Configuration

Enable Home Assistant discovery:

```yaml
mqtt:
  ha_discovery:
    enabled: yes
```

To modify the announcements for individual inputs/outputs/sensors more appropriate, add the `ha_discovery` section to their config entries and add entries [as specified in the HA docs](https://www.home-assistant.io/docs/mqtt/discovery/)

### Example

```yaml
mqtt:
  host: localhost
  ha_discovery:
    enabled: yes

gpio_modules:
  - name: rpi
    module: raspberrypi

digital_inputs:
  - name: door_sensor
    module: rpi
    pin: 1
    ha_discovery:
      name: Front Door
      device_class: door

digital_outputs:
  - name: hall_fan
    module: rpi
    pin: 2
    ha_discovery:
      name: Hall Fan
      device_class: fan
```

### Availability

In order for Home Assistant to establish whether the input/output/sensor is available, it monitors the `state_topic` for `payload_available` and `payload_not_available`. By default, MQTT IO will set this to one of _three_ values depicted in the `mqtt` section as `status_payload_running`, `status_payload_stopped` and `status_payload_dead`. For Home Assistant's availability checking to work correctly, it might be worth changing your status payloads to be one of _two_ values instead:

```yaml
mqtt:
  host: localhost
  status_payload_running: available
  status_payload_stopped: unavailable
  status_payload_dead: unavailable
```

Unless set specifically in the `ha_discovery` section of the input/output/sensor configs, `payload_available` will be set to the value of `mqtt.status_payload_running` and `payload_not_available` will be set to the value of `mqtt.status_payload_dead`.

## Implementation

After connecting to the MQTT server, MQTT IO will announce digital inputs, digital outputs and sensors to Home Assistant by publishing a JSON payload containing details of the input/output/sensor to the Home Assistant discovery topics. For example, the following JSON might be sent to the `homeassistant/binary_sensor/pi-mqtt-gpio-429373a4/button/config` topic for a digital input:

```json
{
  "name": "button",
  "unique_id": "pi-mqtt-gpio-429373a4_stdio_input_button",
  "state_topic": "pimqttgpio/mydevice/input/button",
  "availability_topic": "pimqttgpio/mydevice/status",
  "payload_available": "running",
  "payload_not_available": "dead",
  "payload_on": "ON",
  "payload_off": "OFF",
  "device": {
    "manufacturer": "MQTT IO",
    "identifiers": [
      "mqtt-gpio",
      "pi-mqtt-gpio-429373a4"
    ],
    "name": "MQTT IO"
  }
}
```
