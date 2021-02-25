# SPDX-FileCopyrightText: 2020 Dan Halbert for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_ble_adafruit.proximity_service`
================================================================================

BLE access to proximity sensor.

* Author(s): Dan Halbert
"""
__version__ = "1.2.3"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_BLE_Adafruit.git"

from adafruit_ble.attributes import Attribute
from adafruit_ble.characteristics import Characteristic
from adafruit_ble.characteristics.int import Uint16Characteristic
from adafruit_ble_adafruit.adafruit_service import AdafruitService


class ProximityService(AdafruitService):  # pylint: disable=too-few-public-methods
    """Status of buttons and switches on the board."""

    uuid = AdafruitService.adafruit_service_uuid(0xE00)
    proximity = Uint16Characteristic(
        uuid=AdafruitService.adafruit_service_uuid(0xE01),
        properties=(Characteristic.READ | Characteristic.NOTIFY),
        read_perm=Attribute.OPEN,
        write_perm=Attribute.NO_ACCESS,
    )
    """
    A higher number indicates a closer distance to the sensor.
    The value is unit-less.
    """
    measurement_period = AdafruitService.measurement_period_charac(0)
    """Initially 0: send notification only on changes. -1 means stop reading."""
