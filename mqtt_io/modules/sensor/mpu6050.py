"""
MPU-6050 Gyroscope / Accelerometer Sensor

Mandatory:
- chip_addr

Output:
- x (in m*s²)
- y (in m*s²)
- z (in m*s²)
"""

from json import dumps
from typing import cast
import smbus
import math
import json

from ...types import CerberusSchemaType, ConfigType, SensorValueType
from . import GenericSensor
from ...exceptions import RuntimeConfigError
import logging

_LOG = logging.getLogger(__name__)

REQUIREMENTS = ("mpu6050",)
CONFIG_SCHEMA: CerberusSchemaType = {
    "chip_addr": {"type": 'integer', "required": True, "empty": False},
}

# MPU6050 Registers

MPU6050_PWR_MGMT_1 = 0x6B
MPU6050_TEMP_OUT_H = 0x41
MPU6050_ACCEL_XOUT_H = 0x3B
MPU6050_ACCEL_YOUT_H = 0x3D
MPU6050_ACCEL_ZOUT_H = 0x3F
MPU6050_GYRO_XOUT_H = 0x43
MPU6050_GYRO_YOUT_H = 0x45
MPU6050_GYRO_ZOUT_H = 0x47

# =============================================================================

class Sensor(GenericSensor):
    """
    Implementation of Sensor class for the MPU6050 sensor.
    """

    SENSOR_SCHEMA: CerberusSchemaType = {
        "type": {
            "type": 'list',
            "required": False,
            "empty": False,
            "default": ['gyro', "angle"],
            "allowed": ['gyro', 'angle', 'accel', 'temp', 'all'],
        },
    }

    def setup_module(self) -> None:
        self.i2c_addr: int = self.config["chip_addr"]
        self.sensor = smbus.SMBus(1)  # or 0 for RPi 1
        self.sensor.write_byte_data(self.i2c_addr, MPU6050_PWR_MGMT_1, 0)

    def get_value(self, sens_conf: ConfigType) -> SensorValueType:
        sens_type = sens_conf["type"]

        # Read raw data from the sensor
        def read_raw_data(addr):
            # Read raw data in a single transaction
            high = self.sensor.read_i2c_block_data(self.i2c_addr, addr, 2)
            value = (high[0] << 8) | high[1]
            if value > 32768:
                value -= 65536
            return value

        # Read sensor data
        accel_x, accel_y, accel_z = [read_raw_data(addr) for addr in (MPU6050_ACCEL_XOUT_H, MPU6050_ACCEL_YOUT_H, MPU6050_ACCEL_ZOUT_H)]
        gyro_x, gyro_y, gyro_z = [read_raw_data(addr) for addr in (MPU6050_GYRO_XOUT_H, MPU6050_GYRO_YOUT_H, MPU6050_GYRO_ZOUT_H)]
        temp = read_raw_data(MPU6050_TEMP_OUT_H)

        # Calculate angles
        x_angle = math.atan(accel_x / 16384.0) * (180 / math.pi)
        y_angle = math.atan(accel_y / 16384.0) * (180 / math.pi)

        # Prepare data dictionary
        data_gyro = {
            "gyro_x": gyro_x,
            "gyro_y": gyro_y,
            "gyro_z": gyro_z,
        }

        data_angle = {
            "angle_x": x_angle,
            "angle_y": y_angle,
        }

        data_accel= {
            "accel_x": accel_x,
            "accel_y": accel_y,
            "accel_z": accel_z,
        }

        data_temp= {
            "temp": (temp / 340.0) + 36.53  # Temperature formula for MPU6050
        }

        data = {}
        if "gyro" in sens_type or "all" in sens_type:
            data.update(data_gyro)
        if "angle" in sens_type or "all" in sens_type:
            data.update(data_angle)
        if "accel" in sens_type or "all" in sens_type:
            data.update(data_accel)
        if "temp" in sens_type or "all" in sens_type:
            data.update(data_temp)

        return data