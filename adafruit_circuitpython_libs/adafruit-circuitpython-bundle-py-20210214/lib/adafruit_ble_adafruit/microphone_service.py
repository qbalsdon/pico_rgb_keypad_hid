# SPDX-FileCopyrightText: 2020 Dan Halbert for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_ble_adafruit.microphone_service`
================================================================================

BLE access to microphone data.

* Author(s): Dan Halbert
"""

__version__ = "1.2.3"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_BLE_Adafruit.git"

from adafruit_ble.attributes import Attribute
from adafruit_ble.characteristics import Characteristic
from adafruit_ble.characteristics.int import Uint8Characteristic
from adafruit_ble_adafruit.adafruit_service import AdafruitService


class MicrophoneService(AdafruitService):  # pylint: disable=too-few-public-methods
    """Digital microphone data."""

    uuid = AdafruitService.adafruit_service_uuid(0xB00)

    sound_samples = Characteristic(
        uuid=AdafruitService.adafruit_service_uuid(0xB01),
        properties=(Characteristic.READ | Characteristic.NOTIFY),
        write_perm=Attribute.NO_ACCESS,
        max_length=512,
    )
    """
    Array of 16-bit sound samples, varying based on period.
    If num_channel == 2, the samples alternate left and right channels.
    """

    number_of_channels = Uint8Characteristic(
        uuid=AdafruitService.adafruit_service_uuid(0xB02),
        properties=Characteristic.READ,
        write_perm=Attribute.NO_ACCESS,
    )
    """1 for mono, 2 for stereo (left and right)"""

    measurement_period = AdafruitService.measurement_period_charac()
    """Initially 1000ms."""
