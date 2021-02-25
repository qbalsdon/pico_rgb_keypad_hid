# SPDX-FileCopyrightText: 2016 Damien P. George (original Neopixel object)
# SPDX-FileCopyrightText: 2017 Ladyada for Adafruit Industries
# SPDX-FileCopyrightText: 2017 Scott Shawcroft for Adafruit Industries
# SPDX-FileCopyrightText: 2018 Kevin J. Walters
#
# SPDX-License-Identifier: MIT

"""
`adafruit_ws2801` - WS2801 LED pixel string driver
====================================================

* Author(s): Damien P. George, Limor Fried & Scott Shawcroft, Kevin J Walters
"""
import math

import busio
import digitalio

__version__ = "0.10.5"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_WS2801.git"

### based on https://github.com/adafruit/Adafruit_CircuitPython_DotStar


class WS2801:
    """
    A sequence of WS2801 controlled LEDs.

    :param ~microcontroller.Pin clock: The pin to output dotstar clock on.
    :param ~microcontroller.Pin data: The pin to output dotstar data on.
    :param int n: The number of LEDs in the chain.
    :param float brightness: The brightness between 0.0 and (default) 1.0.
    :param bool auto_write: True if the dotstars should immediately change when
        set. If False, `show` must be called explicitly.


    Example for Gemma M0:

    .. code-block:: python

        import adafruit_ws2801
        import time
        import board

        darkred = 0x100000

        with adafruit_ws2801.WS2801(board.D2, board.D0, 25, brightness=1.0) as pixels:
            pixels[0] = darkred
            time.sleep(2)
    """

    def __init__(self, clock, data, n, *, brightness=1.0, auto_write=True):
        self._spi = None
        try:
            self._spi = busio.SPI(clock, MOSI=data)
            while not self._spi.try_lock():
                pass
            self._spi.configure(baudrate=1000 * 1000)
        except ValueError:
            self.dpin = digitalio.DigitalInOut(data)
            self.cpin = digitalio.DigitalInOut(clock)
            self.dpin.direction = digitalio.Direction.OUTPUT
            self.cpin.direction = digitalio.Direction.OUTPUT
            self.cpin.value = False
        self._n = n
        self._buf = bytearray(n * 3)
        self._brightness = 1.0  ### keeps pylint happy
        # Set auto_write to False temporarily so brightness setter does _not_
        # call show() while in __init__.
        self.auto_write = False
        self.brightness = brightness
        self.auto_write = auto_write
        ### TODO - review/consider adding GRB support like that in c++ version

    def deinit(self):
        """Blank out the DotStars and release the resources."""
        self.auto_write = False
        black = (0, 0, 0)
        self.fill(black)
        self.show()
        if self._spi:
            self._spi.deinit()
        else:
            self.dpin.deinit()
            self.cpin.deinit()

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        self.deinit()

    def __repr__(self):
        return "[" + ", ".join([str(x) for x in self]) + "]"

    def _set_item(self, index, value):
        offset = index * 3
        if isinstance(value, int):
            r = value >> 16
            g = (value >> 8) & 0xFF
            b = value & 0xFF
        else:
            r, g, b = value
        # red/green/blue order for WS2801
        self._buf[offset] = r
        self._buf[offset + 1] = g
        self._buf[offset + 2] = b

    def __setitem__(self, index, val):
        if isinstance(index, slice):
            start, stop, step = index.indices(self._n)
            length = stop - start
            if step != 0:
                length = math.ceil(length / step)
            if len(val) != length:
                raise ValueError("Slice and input sequence size do not match.")
            for val_i, in_i in enumerate(range(start, stop, step)):
                self._set_item(in_i, val[val_i])
        else:
            self._set_item(index, val)

        if self.auto_write:
            self.show()

    def __getitem__(self, index):
        if isinstance(index, slice):
            out = []
            for in_i in range(*index.indices(self._n)):
                out.append(tuple(self._buf[in_i * 3 + i] for i in range(3)))
            return out
        if index < 0:
            index += len(self)
        if index >= self._n or index < 0:
            raise IndexError
        offset = index * 3
        return tuple(self._buf[offset + i] for i in range(3))

    def __len__(self):
        return self._n

    @property
    def brightness(self):
        """Overall brightness of the pixel"""
        return self._brightness

    @brightness.setter
    def brightness(self, brightness):
        self._brightness = min(max(brightness, 0.0), 1.0)
        if self.auto_write:
            self.show()

    def fill(self, color):
        """Colors all pixels the given ***color***."""
        auto_write = self.auto_write
        self.auto_write = False
        for i, _ in enumerate(self):
            self[i] = color
        if auto_write:
            self.show()
        self.auto_write = auto_write

    def _ds_writebytes(self, buf):
        for b in buf:
            for _ in range(8):
                self.dpin.value = b & 0x80
                self.cpin.value = True
                self.cpin.value = False
                b = b << 1

    def show(self):
        """Shows the new colors on the pixels themselves if they haven't already
        been autowritten.

        The colors may or may not be showing after this function returns because
        it may be done asynchronously."""
        # Create a second output buffer if we need to compute brightness
        buf = self._buf
        if self.brightness < 1.0:
            buf = bytearray(len(self._buf))
            for i in range(len(self._buf)):
                buf[i] = int(self._buf[i] * self._brightness)

        if self._spi:
            self._spi.write(buf)
        else:
            self._ds_writebytes(buf)
            self.cpin.value = False
