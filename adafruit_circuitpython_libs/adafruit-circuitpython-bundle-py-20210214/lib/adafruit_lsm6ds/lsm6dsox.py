# SPDX-FileCopyrightText: Copyright (c) 2020 Bryan Siepert for Adafruit Industries
#
# SPDX-License-Identifier: MIT
"""
This module provides the LSM6DSOX subclass of LSM6DS for using LSM6DSOX sensors.
"""
from . import LSM6DS, LSM6DS_DEFAULT_ADDRESS, LSM6DS_CHIP_ID


class LSM6DSOX(LSM6DS):  # pylint: disable=too-many-instance-attributes

    """Driver for the LSM6DSOX 6-axis accelerometer and gyroscope.

        :param ~busio.I2C i2c_bus: The I2C bus the LSM6DSOX is connected to.
        :param address: The I2C slave address of the sensor

    """

    CHIP_ID = LSM6DS_CHIP_ID

    def __init__(self, i2c_bus, address=LSM6DS_DEFAULT_ADDRESS):
        super().__init__(i2c_bus, address)
        self._i3c_disable = True
