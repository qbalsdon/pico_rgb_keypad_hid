# SPDX-FileCopyrightText: 2020 Dan Halbert for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_ble_adafruit.accelerometer_service`
================================================================================

BLE access to accelerometer data.

* Author(s): Dan Halbert
"""

__version__ = "1.2.3"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_BLE_Adafruit.git"

from adafruit_ble.attributes import Attribute
from adafruit_ble.characteristics import Characteristic, StructCharacteristic
from adafruit_ble_adafruit.adafruit_service import AdafruitService


class AccelerometerService(AdafruitService):  # pylint: disable=too-few-public-methods
    """Accelerometer values."""

    uuid = AdafruitService.adafruit_service_uuid(0x200)
    acceleration = StructCharacteristic(
        "<fff",
        uuid=AdafruitService.adafruit_service_uuid(0x201),
        properties=(Characteristic.READ | Characteristic.NOTIFY),
        write_perm=Attribute.NO_ACCESS,
    )
    """Tuple (x, y, z) float acceleration values, in m/s^2"""

    measurement_period = AdafruitService.measurement_period_charac()
    """Initially 1000ms."""
