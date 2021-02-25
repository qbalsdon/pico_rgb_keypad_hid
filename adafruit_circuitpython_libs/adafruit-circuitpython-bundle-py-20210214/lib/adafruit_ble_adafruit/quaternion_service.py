# SPDX-FileCopyrightText: 2020 Dan Halbert for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_ble_adafruit.quaternion_service`
================================================================================

BLE access to quaternion data.

* Author(s): Dan Halbert
"""

__version__ = "1.2.3"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_BLE_Adafruit.git"

from adafruit_ble.attributes import Attribute
from adafruit_ble.characteristics import Characteristic, StructCharacteristic
from adafruit_ble_adafruit.adafruit_service import AdafruitService


class QuaternionService(AdafruitService):  # pylint: disable=too-few-public-methods
    """Quaternion values."""

    uuid = AdafruitService.adafruit_service_uuid(0xD00)
    quaternion = StructCharacteristic(
        "<ffff",
        uuid=AdafruitService.adafruit_service_uuid(0xD01),
        properties=(Characteristic.READ | Characteristic.NOTIFY),
        write_perm=Attribute.NO_ACCESS,
    )
    """Tuple (qw, qx, qy, qz) of float quaternion values."""
    measurement_period = AdafruitService.measurement_period_charac()
    """Initially 1000ms."""

    calibration_in = StructCharacteristic(
        "<fffffffff",
        uuid=AdafruitService.adafruit_service_uuid(0xD02),
        properties=(Characteristic.READ | Characteristic.NOTIFY),
        write_perm=Attribute.NO_ACCESS,
    )
    """
    9-tuple of floats sent to client for calibration calculation:
    acceleration x, y, z,  # in m/s^2
    gyro x, y, z,   # in rad/s
    magnetic x, y, z,   # in microteslas
    """

    calibration_out = StructCharacteristic(
        "<fffffffffffffffffff",
        uuid=AdafruitService.adafruit_service_uuid(0xD03),
        properties=(Characteristic.WRITE),
        read_perm=Attribute.NO_ACCESS,
    )
    """
    19-tuple of floats sent back to server after calibration calculation:
    acceleration_zerog x, y, z,  # in m/s^2
    gyro_zerorate x, y, z,   # in rad/s
    magnetic_hardiron x, y, z,   # in microteslas
    magnetic_field f,  # in microteslas
    magnetic_softiron v1, v2, v3, v4, v5, v6, v7, v8, v9,   # unitless
    """

    # TO DO: Calibration calculations and storage
