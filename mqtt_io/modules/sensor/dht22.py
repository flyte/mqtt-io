"""
Sensor module for DHT22.
"""

from ...exceptions import RuntimeConfigError
from ...types import CerberusSchemaType, ConfigType, PinType, SensorValueType
from . import GenericSensor

REQUIREMENTS = ("Adafruit_DHT",)
ALLOWED_TYPES = ["dht11", "dht22", "am2302"]
CONFIG_SCHEMA: CerberusSchemaType = {
    "pin": dict(type="integer", required=True, empty=False),
    "type": dict(
        type="string",
        required=True,
        empty=False,
        allowed=ALLOWED_TYPES + [x.upper() for x in ALLOWED_TYPES],
    ),
}


class Sensor(GenericSensor):
    """
    Implementation of Sensor class for the DHT22 temperature sensor.
    """

    SENSOR_SCHEMA: CerberusSchemaType = {
        "type": dict(
            type="string",
            required=False,
            empty=False,
            default="temperature",
            allowed=["temperature", "humidity"],
        )
    }

    def setup_module(self) -> None:
        # pylint: disable=import-outside-toplevel,import-error
        import Adafruit_DHT as DHTsensor  # type: ignore

        sensor_type: str = self.config["type"].lower()

        self.sensor_type: int
        if sensor_type == "dht22":
            self.sensor_type = DHTsensor.DHT22
        elif sensor_type == "dht11":
            self.sensor_type = DHTsensor.DHT11
        elif sensor_type == "am2302":
            self.sensor_type = DHTsensor.AM2302
        else:
            raise RuntimeConfigError("Supported sensor types: DHT22, DHT11, AM2302")

        self.pin: PinType = self.config["pin"]
        self.sensor = DHTsensor

    def get_value(self, sens_conf: ConfigType) -> SensorValueType:
        """
        Get the temperature or humidity value from the sensor
        """
        humidity: SensorValueType
        temperature: SensorValueType
        humidity, temperature = self.sensor.read_retry(self.sensor_type, self.pin)
        if sens_conf["type"] == "temperature":
            return temperature
        if sens_conf["type"] == "humidity":
            return humidity
        raise RuntimeConfigError(
            "dht22 sensor '%s' was not configured to return 'temperature' or 'humidity'"
            % sens_conf["name"]
        )
