"""
DHT11/DHT22/AM2302 temperature and humidity sensors
"""

from ...exceptions import RuntimeConfigError
from ...types import CerberusSchemaType, ConfigType, PinType, SensorValueType
from . import GenericSensor

REQUIREMENTS = ("adafruit-circuitpython-dht",)
ALLOWED_TYPES = ["dht11", "dht22", "am2302"]
CONFIG_SCHEMA: CerberusSchemaType = {
    "pin": {"type": 'integer', "required": True, "empty": False},
    "type": {
        "type": 'string',
        "required": True,
        "empty": False,
        "allowed": ALLOWED_TYPES + [x.upper() for x in ALLOWED_TYPES],
    },
}


class Sensor(GenericSensor):
    """
    Implementation of Sensor class for the DHT22 temperature sensor.
    """

    SENSOR_SCHEMA: CerberusSchemaType = {
        "type": {
            "type": 'string',
            "required": False,
            "empty": False,
            "default": 'temperature',
            "allowed": ['temperature', 'humidity'],
        }
    }

    def setup_module(self) -> None:
        # pylint: disable=import-outside-toplevel,import-error
        import adafruit_dht  # type: ignore
        from microcontroller import Pin # type: ignore

        sensor_type: str = self.config["type"].lower()

        if sensor_type == "dht22":
            self.sensor = adafruit_dht.DHT22
        elif sensor_type == "dht11":
            self.sensor = adafruit_dht.DHT11
        elif sensor_type == "am2302":
            self.sensor = adafruit_dht.DHT21
        else:
            raise RuntimeConfigError("Supported sensor types: DHT22, DHT11 and AM2302/DHT21")

        self.pin: PinType = Pin(self.config["pin"])

    def get_value(self, sens_conf: ConfigType) -> SensorValueType:
        """
        Get the temperature or humidity value from the sensor
        """
        humidity: SensorValueType
        temperature: SensorValueType
        dht_device = self.sensor(self.pin, use_pulseio=False)
        humidity, temperature = dht_device.humidity, dht_device.temperature
        if sens_conf["type"] == "temperature":
            return temperature
        if sens_conf["type"] == "humidity":
            return humidity
        raise RuntimeConfigError(
            "dht22 sensor '%s' was not configured to return 'temperature' or 'humidity'"
            % sens_conf["name"]
        )
