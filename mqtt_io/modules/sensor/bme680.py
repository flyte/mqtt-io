"""
BME680 temperature, humidity, and pressure sensor
"""

from typing import cast
import logging
import time
from ...types import CerberusSchemaType, ConfigType, SensorValueType
from . import GenericSensor

_LOG = logging.getLogger(__name__)

REQUIREMENTS = ("smbus2", "bme680")
CONFIG_SCHEMA = {
    "i2c_bus_num": dict(type="integer", required=False, empty=False),
    "chip_addr": dict(type="integer", required=True, empty=False),
    "filter_size": dict(type="integer", required=False, empty=False, default=3),
}

class Sensor(GenericSensor):
    """
    Implementation of Sensor class for the BME680 sensor.
    """

    SENSOR_SCHEMA: CerberusSchemaType = {
        "type": dict(
            type="string",
            required=False,
            default="temperature",
            allowed=["temperature", "humidity", "pressure", "gas", "air_quality"],
        ),
        "oversampling": dict(
            type="string",
            required=False,
            allowed=["none", "1x", "2x", "4x", "8x", "16x"],
        ),
    }

    def setup_module(self) -> None:
        # pylint: disable=import-outside-toplevel,attribute-defined-outside-init
        # pylint: disable=import-error,no-member
        from smbus2 import SMBus  # type: ignore
        import bme680  # type: ignore

        self.i2c_addr: int = self.config["chip_addr"]
        self.i2c_device = SMBus(self.config["i2c_bus_num"])
        self.sensor = bme680.BME680(self.i2c_addr, self.i2c_device)

        self.filter_map = {
            "0": bme680.FILTER_SIZE_0,
            "1": bme680.FILTER_SIZE_1,
            "3": bme680.FILTER_SIZE_3,
            "7": bme680.FILTER_SIZE_7,
            "15": bme680.FILTER_SIZE_15,
            "31": bme680.FILTER_SIZE_31,
            "63": bme680.FILTER_SIZE_63,
            "127": bme680.FILTER_SIZE_127,
        }

        set_filter_size = getattr(self.sensor, "set_filter")
        set_filter_size(self.filter_map[str(self.config["filter_size"])])

        self.oversampling_map = {
            "none": bme680.OS_NONE,
            "1x": bme680.OS_1X,
            "2x": bme680.OS_2X,
            "4x": bme680.OS_4X,
            "8x": bme680.OS_8X,
            "16x": bme680.OS_16X,
        }

        self.gas_map = {
            "enabled": bme680.ENABLE_GAS_MEAS,
        }

        self.gas_baseline = None

    def gas_avg(self, burn_in_time) -> float:
        """
        Calculate the average gas resistance.
        :return: Gas Resistance
        """

        start_time = time.time()
        curr_time = time.time()

        burn_in_data = []
        _LOG.info(("Beginning %d seconds gas sensor burn"), burn_in_time)
        while curr_time - start_time < burn_in_time:
            curr_time = time.time()
            if self.sensor.get_sensor_data() and self.sensor.data.heat_stable:
                gas = self.sensor.data.gas_resistance
                burn_in_data.append(gas)
                time.sleep(1)
        gas = sum(burn_in_data[-50:]) / 50.0
        _LOG.info("Gas Resistance : %f", gas)
        return gas

    def setup_sensor(self, sens_conf: ConfigType) -> None:
        """
        Setup the BME680 sensor with the provided configuration.
        :param sens_conf: Configuration for the sensor.
        """
        sens_type: str = sens_conf["type"]
        if "oversampling" in sens_conf:
            # Set oversampling directly based on the sensor type
            oversampling = self.oversampling_map.get(sens_conf["oversampling"])
            if oversampling is not None:
                getattr(self.sensor, f"set_{sens_type}_oversample")(oversampling)

        if "gas" in sens_type or "air_quality" in sens_type:
            # Set gas related parameters for gas and air quality measurements
            getattr(self.sensor, "set_gas_status")(self.gas_map["enabled"])
            self.sensor.set_gas_heater_temperature(320)
            self.sensor.set_gas_heater_duration(150)
            self.sensor.select_gas_heater_profile(0)

        if "air_quality" in sens_type:
            # pylint: disable=attribute-defined-outside-init
            self.gas_baseline = self.gas_avg(300)

    def air_quality(self) -> float:
        """
        Calculate the air quality score based on humidity and gas resistance.
        :return: Air quality score.
        """
        gas = self.gas_avg(120)

        gas_baseline = self.gas_baseline
        # Set the humidity baseline to 40%, an optimal indoor humidity.
        hum_baseline = 40.0

        # This sets the balance between humidity and gas reading in the
        # calculation of air_quality_score (25:75, humidity:gas)
        hum_weighting = 0.25

        gas_offset = gas_baseline - gas

        hum = self.sensor.data.humidity
        hum_offset = hum - hum_baseline

        # Calculate hum_score as the distance from the hum_baseline.
        if hum_offset > 0:
            hum_score = (100 - hum_baseline - hum_offset) / (100 - hum_baseline)
            hum_score *= (hum_weighting * 100)
        else:
            hum_score = (hum_baseline + hum_offset) / hum_baseline
            hum_score *= (hum_weighting * 100)

        # Calculate gas_score as the distance from the gas_baseline.
        if gas_offset > 0:
            gas_score = (gas / gas_baseline) * (100 - (hum_weighting * 100))
        else:
            gas_score = 100 - (hum_weighting * 100)

        # Calculate air_quality_score.
        air_quality_score = hum_score + gas_score
        return air_quality_score

    def get_value(self, sens_conf: ConfigType) -> SensorValueType:
        """
        Get the value of the specified sensor type from the BME680 sensor.
        :param sens_conf: Configuration for the sensor.
        :return: Value of the sensor.
        """
        sens_type = sens_conf["type"]

        if not self.sensor.get_sensor_data():
            return None

        if sens_type == "air_quality" and self.sensor.data.heat_stable:
            return self.air_quality()

        if sens_type == "gas" and self.sensor.data.heat_stable:
            return self.gas_avg(120)

        return cast(
            float,
            dict(
                temperature=self.sensor.data.temperature,
                humidity=self.sensor.data.humidity,
                pressure=self.sensor.data.pressure,
            ).get(sens_type),
        )
