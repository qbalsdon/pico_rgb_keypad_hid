# SPDX-FileCopyrightText: Copyright (c) 2020 Bryan Siepert for Adafruit Industries
#
# SPDX-License-Identifier: MIT
"""
This module provides the LSM6DSO32 subclass of LSM6DS for using LSM6DSO32 sensors.
"""
from . import LSM6DS, LSM6DS_CHIP_ID, LSM6DS_DEFAULT_ADDRESS, AccelRange


class LSM6DSO32(LSM6DS):  # pylint: disable=too-many-instance-attributes

    """Driver for the LSM6DSO32 6-axis accelerometer and gyroscope.

        :param ~busio.I2C i2c_bus: The I2C bus the LSM6DSO32 is connected to.
        :param address: The I2C slave address of the sensor

    """

    CHIP_ID = LSM6DS_CHIP_ID

    def __init__(self, i2c_bus, address=LSM6DS_DEFAULT_ADDRESS):
        super().__init__(i2c_bus, address)
        self._i3c_disable = True
        self.accelerometer_range = AccelRange.RANGE_8G  # pylint:disable=no-member

    def _add_accel_ranges(self):
        AccelRange.add_values(
            (
                ("RANGE_4G", 0, 4, 0.122),
                ("RANGE_32G", 1, 32, 0.976),
                ("RANGE_8G", 2, 8, 0.244),
                ("RANGE_16G", 3, 16, 0.488),
            )
        )
