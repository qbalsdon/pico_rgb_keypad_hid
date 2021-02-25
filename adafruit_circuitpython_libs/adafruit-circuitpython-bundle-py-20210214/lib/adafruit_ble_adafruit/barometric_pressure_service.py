# SPDX-FileCopyrightText: 2020 Dan Halbert for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_ble_adafruit.barometric_pressure_service`
================================================================================

BLE access to barometric pressure data.

* Author(s): Dan Halbert
"""

__version__ = "1.2.3"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_BLE_Adafruit.git"

from adafruit_ble.attributes import Attribute
from adafruit_ble.characteristics import Characteristic
from adafruit_ble.characteristics.float import FloatCharacteristic
from adafruit_ble_adafruit.adafruit_service import AdafruitService


class BarometricPressureService(
    AdafruitService
):  # pylint: disable=too-few-public-methods
    """Barometric pressure value."""

    uuid = AdafruitService.adafruit_service_uuid(0x800)
    pressure = FloatCharacteristic(
        uuid=AdafruitService.adafruit_service_uuid(0x801),
        properties=(Characteristic.READ | Characteristic.NOTIFY),
        write_perm=Attribute.NO_ACCESS,
    )
    """Barometric pressure in hectoPascals (hPa) (float)"""
    measurement_period = AdafruitService.measurement_period_charac()
    """Initially 1000ms."""
