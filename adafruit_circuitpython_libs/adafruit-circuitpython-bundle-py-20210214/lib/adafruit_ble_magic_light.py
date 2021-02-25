# SPDX-FileCopyrightText: 2019 Scott Shawcroft for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
:py:mod:`~adafruit_ble.services.magic_light`
====================================================

This module provides Services available on a Magic Light, BLE RGB light bulb.

"""

from adafruit_ble.services import Service
from adafruit_ble.uuid import VendorUUID
from adafruit_ble.characteristics import Characteristic

__version__ = "0.9.6"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_BLE_Magic_Light.git"


class MagicLightService(Service):
    """Service for controlling a Magic Light RGB bulb."""

    # These UUIDs actually use the standard base UUID even though they aren't standard.
    uuid = VendorUUID("0000ffe5-0000-1000-8000-00805f9b34fb")

    _control = Characteristic(
        uuid=VendorUUID("0000ffe9-0000-1000-8000-00805f9b34fb"), max_length=7
    )

    def __init__(self, service=None):
        super().__init__(service=service)
        self._color = 0xFFFFFF
        self._buf = bytearray(7)
        self._buf[0] = 0x56
        self._buf[6] = 0xAA
        self._brightness = 1.0

    def __getitem__(self, index):
        if index > 0:
            raise IndexError()
        return self._color

    def __setitem__(self, index, value):
        if index > 0:
            raise IndexError()
        if isinstance(value, int):
            r = (value >> 16) & 0xFF
            g = (value >> 8) & 0xFF
            b = value & 0xFF
        else:
            r, g, b = value
        self._buf[1] = r
        self._buf[2] = g
        self._buf[3] = b
        self._buf[4] = 0x00
        self._buf[5] = 0xF0
        self._control = self._buf
        self._color = value

    def __len__(self):
        return 1

    # Brightness doesn't preserve the color so comment it out for now. There are many other
    # characteristics to try that may.
    # @property
    # def brightness(self):
    #     return self._brightness
    #
    # @brightness.setter
    # def brightness(self, value):
    #     for i in range(3):
    #         self._buf[i + 1] = 0x00
    #     self._buf[4] = int(0xff * value)
    #     self._buf[5] = 0x0f
    #     self._control = self._buf
    #     self._brightness = value
