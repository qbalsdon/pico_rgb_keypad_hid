# SPDX-FileCopyrightText: 2020 Dan Halbert for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_ble_adafruit.light_sensor_service`
================================================================================

BLE access to light sensor data.

* Author(s): Dan Halbert
"""

__version__ = "1.2.3"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_BLE_Adafruit.git"

from adafruit_ble.attributes import Attribute
from adafruit_ble.characteristics import Characteristic
from adafruit_ble.characteristics.float import FloatCharacteristic
from adafruit_ble_adafruit.adafruit_service import AdafruitService


class LightSensorService(AdafruitService):  # pylint: disable=too-few-public-methods
    """Light sensor value."""

    uuid = AdafruitService.adafruit_service_uuid(0x300)
    light_level = FloatCharacteristic(
        uuid=AdafruitService.adafruit_service_uuid(0x301),
        properties=(Characteristic.READ | Characteristic.NOTIFY),
        write_perm=Attribute.NO_ACCESS,
    )
    """Uncalibrated light level (float)"""
    measurement_period = AdafruitService.measurement_period_charac()
    """Initially 1000ms."""
