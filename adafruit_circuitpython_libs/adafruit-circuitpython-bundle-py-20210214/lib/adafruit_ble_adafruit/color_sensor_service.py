# SPDX-FileCopyrightText: 2020 Dan Halbert for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_ble_adafruit.color_sensor_service`
================================================================================

BLE access to color sensor data.

* Author(s): Dan Halbert
"""

__version__ = "1.2.3"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_BLE_Adafruit.git"

from adafruit_ble.attributes import Attribute
from adafruit_ble.characteristics import Characteristic, StructCharacteristic
from adafruit_ble_adafruit.adafruit_service import AdafruitService


class ColorSensorService(AdafruitService):  # pylint: disable=too-few-public-methods
    """Color sensor value."""

    uuid = AdafruitService.adafruit_service_uuid(0xA00)
    acceleration = StructCharacteristic(
        "<HHH",
        uuid=AdafruitService.adafruit_service_uuid(0xA01),
        properties=(Characteristic.READ | Characteristic.NOTIFY),
        write_perm=Attribute.NO_ACCESS,
    )
    """Tuple (r, g, b) red/green/blue color values, each in range 0-65535 (16 bits)"""

    measurement_period = AdafruitService.measurement_period_charac()
    """Initially 1000ms."""
