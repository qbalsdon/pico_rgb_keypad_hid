# SPDX-FileCopyrightText: 2018 ladyada for Adafruit Industries
#
# SPDX-License-Identifier: MIT

# pylint: disable=line-too-long
"""
`adafruit_sharpmemorydisplay`
====================================================

A display control library for Sharp 'memory' displays

* Author(s): ladyada

Implementation Notes
--------------------

**Hardware:**

* `Adafruit SHARP Memory Display Breakout - 1.3 inch 144x168 Monochrome <https://www.adafruit.com/product/3502>`_

* `Adafruit SHARP Memory Display Breakout - 1.3 inch 96x96 Monochrome <https://www.adafruit.com/product/1393>`_

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://github.com/adafruit/circuitpython/releases

"""
# pylint: enable=line-too-long

from micropython import const
import adafruit_framebuf

__version__ = "1.2.6"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_SharpMemoryDisplay.git"

_SHARPMEM_BIT_WRITECMD = const(0x80)  # in lsb
_SHARPMEM_BIT_VCOM = const(0x40)  # in lsb
_SHARPMEM_BIT_CLEAR = const(0x20)  # in lsb


def reverse_bit(num):
    """Turn an LSB byte to an MSB byte, and vice versa. Used for SPI as
    it is LSB for the SHARP, but 99% of SPI implementations are MSB only!"""
    result = 0
    for _ in range(8):
        result <<= 1
        result += num & 1
        num >>= 1
    return result


class SharpMemoryDisplay(adafruit_framebuf.FrameBuffer):
    """A driver for sharp memory displays, you can use any size but the
    full display must be buffered in memory!"""

    # pylint: disable=too-many-instance-attributes,abstract-method

    def __init__(self, spi, scs_pin, width, height, *, baudrate=2000000):
        self._scs_pin = scs_pin
        scs_pin.switch_to_output(value=True)
        self._baudrate = baudrate
        # The SCS pin is active HIGH so we can't use bus_device. exciting!
        self._spi = spi
        # prealloc for when we write the display
        self._buf = bytearray(1)

        # even tho technically this display is LSB, we have to flip the bits
        # when writing out SPI so lets just do flipping once, in the buffer
        self.buffer = bytearray((width // 8) * height)
        super().__init__(self.buffer, width, height, buf_format=adafruit_framebuf.MHMSB)

        # Set the vcom bit to a defined state
        self._vcom = True

    def show(self):
        """write out the frame buffer via SPI, we use MSB SPI only so some
        bit-swapping is rquired. The display also uses inverted CS for some
        reason so we con't use bus_device"""

        # CS pin is inverted so we have to do this all by hand
        while not self._spi.try_lock():
            pass
        self._spi.configure(baudrate=self._baudrate)
        self._scs_pin.value = True

        # toggle the VCOM bit
        self._buf[0] = _SHARPMEM_BIT_WRITECMD
        if self._vcom:
            self._buf[0] |= _SHARPMEM_BIT_VCOM
        self._vcom = not self._vcom
        self._spi.write(self._buf)

        slice_from = 0
        line_len = self.width // 8
        for line in range(self.height):
            self._buf[0] = reverse_bit(line + 1)
            self._spi.write(self._buf)
            self._spi.write(memoryview(self.buffer[slice_from : slice_from + line_len]))
            slice_from += line_len
            self._buf[0] = 0
            self._spi.write(self._buf)
        self._spi.write(self._buf)  # we send one last 0 byte
        self._scs_pin.value = False
        self._spi.unlock()
