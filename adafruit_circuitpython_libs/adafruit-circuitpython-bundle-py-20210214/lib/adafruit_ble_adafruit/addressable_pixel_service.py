# SPDX-FileCopyrightText: 2020 Dan Halbert for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_ble_adafruit.addressable_pixel_service`
================================================================================

BLE control of addressable pixels, such as NeoPixels or DotStars.

* Author(s): Dan Halbert
"""

__version__ = "1.2.3"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_BLE_Adafruit.git"

from collections import namedtuple
import struct

import _bleio

from adafruit_ble.attributes import Attribute
from adafruit_ble.characteristics import Characteristic, ComplexCharacteristic
from adafruit_ble.characteristics.int import Uint8Characteristic, Uint16Characteristic
from adafruit_ble_adafruit.adafruit_service import AdafruitService

PixelValues = namedtuple(
    "PixelValues",
    ("start", "write_now", "data"),
)
"""Namedtuple for pixel data and instructions.

* start

    start writing data into buffer at this byte number (byte, not pixel)

* write_now

    ``True`` if data should be written to pixels now.
    ``False`` if write should not happen immediately.

* data

    sequence of bytes of data for all pixels, in proper color order for type of pixel
"""


class _PixelPacket(ComplexCharacteristic):
    """
    start: uint16: start writing data into buffer at this byte number (byte, not pixel)
    flags: uint8: bit 0: 0 = don't write to pixels yet
                         1 = write entire buffer to pixels now
    data: raw array of data for all pixels, in proper color order for type of pixel
    """

    MAX_LENGTH = 512

    uuid = AdafruitService.adafruit_service_uuid(0x903)

    def __init__(self):
        super().__init__(
            properties=Characteristic.WRITE,
            read_perm=Attribute.NO_ACCESS,
            max_length=self.MAX_LENGTH,
        )

    def bind(self, service):
        """Binds the characteristic to the given Service."""
        bound_characteristic = super().bind(service)
        return _bleio.PacketBuffer(bound_characteristic, buffer_size=1)


class AddressablePixelService(AdafruitService):
    """Control of NeoPixels, DotStars, etc."""

    uuid = AdafruitService.adafruit_service_uuid(0x900)
    pixel_pin = Uint8Characteristic(
        uuid=AdafruitService.adafruit_service_uuid(0x901),
        properties=(Characteristic.READ | Characteristic.WRITE),
    )
    """Send data out on this pin."""

    pixel_pin_type = Uint8Characteristic(
        uuid=AdafruitService.adafruit_service_uuid(0x902),
        properties=(Characteristic.READ | Characteristic.WRITE),
    )

    pixel_buffer_size = Uint16Characteristic(
        uuid=AdafruitService.adafruit_service_uuid(0x904),
        properties=(Characteristic.READ | Characteristic.WRITE),
        initial_value=_PixelPacket.MAX_LENGTH,
    )

    """
    0 = WS2812 (NeoPixel), 800kHz
    1 = SPI (APA102: DotStar)
    """
    _pixel_packet = _PixelPacket()
    """Pixel-setting data."""

    def __init__(self, service=None):
        self._pixel_packet_buf = bytearray(_PixelPacket.MAX_LENGTH)
        super().__init__(service=service)

    @property
    def values(self):
        """Return a tuple (start, write_now, data) corresponding to the
        different parts of ``_pixel_packet``.
        """
        buf = self._pixel_packet_buf
        num_read = self._pixel_packet.readinto(buf)  # pylint: disable=no-member
        if num_read == 0:
            # No new values available
            return None

        return PixelValues(
            struct.unpack_from("<H", buf)[0],
            bool(buf[2] & 0x1),
            buf[3:num_read],
        )
