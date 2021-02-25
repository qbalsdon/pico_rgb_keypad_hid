# SPDX-FileCopyrightText: 2020 Dan Halbert for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_ble_adafruit.gesture_service`
================================================================================

BLE access to gesture detector.

* Author(s): Dan Halbert
"""
__version__ = "1.2.3"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_BLE_Adafruit.git"

from adafruit_ble.attributes import Attribute
from adafruit_ble.characteristics import Characteristic
from adafruit_ble.characteristics.int import Uint8Characteristic
from adafruit_ble_adafruit.adafruit_service import AdafruitService


class GestureService(AdafruitService):  # pylint: disable=too-few-public-methods
    """Gesture sensor."""

    UP = 1  # pylint: disable=invalid-name
    """swipe up"""
    DOWN = 2
    """swipe down"""
    LEFT = 3
    """swipe left"""
    RIGHT = 4
    """swipe right"""

    uuid = AdafruitService.adafruit_service_uuid(0xF00)
    gesture = Uint8Characteristic(
        uuid=AdafruitService.adafruit_service_uuid(0xF01),
        properties=(Characteristic.READ | Characteristic.NOTIFY),
        read_perm=Attribute.OPEN,
        write_perm=Attribute.NO_ACCESS,
    )
    """
    0: no gesture
    1: swipe up (`UP`)
    2: swipe down (`DOWN`)
    3: swipe left (`LEFT`)
    4: swipe right (`RIGHT`)
    """
    measurement_period = AdafruitService.measurement_period_charac(0)
    """Initially 0: send notification only on changes. -1 means stop reading."""
