# SPDX-FileCopyrightText: Copyright (c) 2020 Bryan Siepert for Adafruit Industries
#
# SPDX-License-Identifier: MIT
"""
This module provides the ISM330DHCX subclass of LSM6DS for using ISM330DHCX sensors.
"""
from time import sleep
from . import LSM6DS, LSM6DS_DEFAULT_ADDRESS, GyroRange, RWBit, const

_LSM6DS_CTRL2_G = const(0x11)


class ISM330DHCX(LSM6DS):  # pylint: disable=too-many-instance-attributes

    """Driver for the LSM6DS33 6-axis accelerometer and gyroscope.

        :param ~busio.I2C i2c_bus: The I2C bus the LSM6DS33 is connected to.
        :param address: The I2C slave address of the sensor

    """

    CHIP_ID = 0x6B
    _gyro_range_4000dps = RWBit(_LSM6DS_CTRL2_G, 0)

    def __init__(self, i2c_bus, address=LSM6DS_DEFAULT_ADDRESS):
        GyroRange.add_values(
            (
                ("RANGE_125_DPS", 125, 125, 4.375),
                ("RANGE_250_DPS", 0, 250, 8.75),
                ("RANGE_500_DPS", 1, 500, 17.50),
                ("RANGE_1000_DPS", 2, 1000, 35.0),
                ("RANGE_2000_DPS", 3, 2000, 70.0),
                ("RANGE_4000_DPS", 4000, 4000, 140.0),
            )
        )
        super().__init__(i2c_bus, address)

        # Called DEVICE_CONF in the datasheet, but it recommends setting it
        self._i3c_disable = True

    @property
    def gyro_range(self):
        """Adjusts the range of values that the sensor can measure, from 125 Degrees/s to 4000
        degrees/s. Note that larger ranges will be less accurate. Must be a `GyroRange`. 4000 DPS
        is only available for the ISM330DHCX"""
        return self._cached_gyro_range

    @gyro_range.setter
    def gyro_range(self, value):
        super()._set_gyro_range(value)

        # range uses the `FS_4000` bit
        if value is GyroRange.RANGE_4000_DPS:  # pylint: disable=no-member
            self._gyro_range_125dps = False
            self._gyro_range_4000dps = True
        else:
            self._gyro_range_4000dps = False

        sleep(0.2)  # needed to let new range settle
