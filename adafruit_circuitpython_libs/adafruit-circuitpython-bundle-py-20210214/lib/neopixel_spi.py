# The MIT License (MIT)
#
# Copyright (c) 2019 Carter Nelson for Adafruit Industries
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
"""
`neopixel_spi`
================================================================================

SPI driven CircuitPython driver for NeoPixels.


* Author(s): Carter Nelson

Implementation Notes
--------------------

**Hardware:**

* Hardware SPI port required on host platform.

**Software and Dependencies:**

* Adafruit Blinka:
  https://github.com/adafruit/Adafruit_Blinka

* Adafruit's Bus Device library: https://github.com/adafruit/Adafruit_CircuitPython_BusDevice
"""

# pylint: disable=ungrouped-imports
import sys
from adafruit_bus_device.spi_device import SPIDevice

if sys.implementation.version[0] < 5:
    import adafruit_pypixelbuf as _pixelbuf
else:
    try:
        import _pixelbuf
    except ImportError:
        import adafruit_pypixelbuf as _pixelbuf

__version__ = "0.9.0"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_NeoPixel_SPI.git"

# Pixel color order constants
RGB = "RGB"
"""Red Green Blue"""
GRB = "GRB"
"""Green Red Blue"""
RGBW = "RGBW"
"""Red Green Blue White"""
GRBW = "GRBW"
"""Green Red Blue White"""


class NeoPixel_SPI(_pixelbuf.PixelBuf):
    """
    A sequence of neopixels.

    :param ~busio.SPI spi: The SPI bus to output neopixel data on.
    :param int n: The number of neopixels in the chain
    :param int bpp: Bytes per pixel. 3 for RGB and 4 for RGBW pixels.
    :param float brightness: Brightness of the pixels between 0.0 and 1.0 where 1.0 is full
      brightness
    :param bool auto_write: True if the neopixels should immediately change when set. If False,
      ``show`` must be called explicitly.
    :param tuple pixel_order: Set the pixel color channel order. GRBW is set by default.
    :param int frequency: SPI bus frequency. For 800kHz NeoPixels, use 6400000 (default).
      For 400kHz, use 3200000.
    :param float reset_time: Reset low level time in seconds. Default is 80e-6.
    :param byte bit0: Bit pattern to set timing for a NeoPixel 0 bit.
    :param byte bit1: Bit pattern to set timing for a NeoPixel 1 bit.

    Example:

    .. code-block:: python

        import board
        import neopixel_spi

        pixels = neopixel_spi.NeoPixel_SPI(board.SPI(), 10)
        pixels.fill(0xff0000)
    """

    def __init__(
        self,
        spi,
        n,
        *,
        bpp=3,
        brightness=1.0,
        auto_write=True,
        pixel_order=None,
        frequency=6400000,
        reset_time=80e-6,
        bit0=0b11000000,
        bit1=0b11110000
    ):

        # configure bpp and pixel_order
        if not pixel_order:
            pixel_order = GRB if bpp == 3 else GRBW
        else:
            bpp = len(pixel_order)
            if isinstance(pixel_order, tuple):
                order_list = [RGBW[order] for order in pixel_order]
                pixel_order = "".join(order_list)

        # neopixel stuff
        self._bit0 = bit0
        self._bit1 = bit1
        self._trst = reset_time

        # set up SPI related stuff
        self._spi = SPIDevice(spi, baudrate=frequency)
        with self._spi as spibus:
            try:
                # get actual SPI frequency
                freq = spibus.frequency
            except AttributeError:
                # use nominal
                freq = frequency
        self._reset = bytes([0] * round(freq * self._trst / 8))
        self._spibuf = bytearray(8 * n * bpp)

        # everything else taken care of by base class
        super().__init__(
            n, brightness=brightness, byteorder=pixel_order, auto_write=auto_write
        )

    def deinit(self):
        """Blank out the NeoPixels."""
        self.fill(0)
        self.show()

    def __repr__(self):
        return "[" + ", ".join([str(x) for x in self]) + "]"

    @property
    def n(self):
        """
        The number of neopixels in the chain (read-only)
        """
        return len(self)

    def _transmit(self, buffer):
        """Shows the new colors on the pixels themselves if they haven't already
        been autowritten."""
        self._transmogrify(buffer)
        # pylint: disable=no-member
        with self._spi as spi:
            # write out special byte sequence surrounded by RESET
            # leading RESET needed for cases where MOSI rests HI
            spi.write(self._reset + self._spibuf + self._reset)

    def _transmogrify(self, buffer):
        """Turn every BIT of buf into a special BYTE pattern."""
        k = 0
        for byte in buffer:
            # MSB first
            for i in range(7, -1, -1):
                if byte >> i & 0x01:
                    self._spibuf[k] = self._bit1  # A NeoPixel 1 bit
                else:
                    self._spibuf[k] = self._bit0  # A NeoPixel 0 bit
                k += 1
