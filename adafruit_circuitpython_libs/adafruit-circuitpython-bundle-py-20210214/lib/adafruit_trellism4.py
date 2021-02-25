# SPDX-FileCopyrightText: 2018 Scott Shawcroft for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_trellism4`
====================================================

CircuitPython library for the Trellis M4 Express.

* Author(s): Scott Shawcroft, Kattni Rembor

Implementation Notes
--------------------

**Hardware:**

# Add link to Trellis M4 Express when product is released.

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://github.com/adafruit/circuitpython/releases


"""

import board
import digitalio
import neopixel
import adafruit_matrixkeypad

__version__ = "1.5.4"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_TrellisM4.git"


class _NeoPixelArray:
    """Creates a NeoPixel array for use in the ``TrellisM4Express`` class."""

    def __init__(self, pin, *, width, height, rotation=0):
        self._neopixel = neopixel.NeoPixel(pin, width * height, auto_write=True)
        if rotation % 90 != 0:
            raise ValueError("Only 90 degree rotations supported")
        self._rotation = rotation % 360
        if self._rotation in (90, 270):
            width, height = height, width
        self._width = width
        self._height = height

    def __setitem__(self, index, value):
        if not isinstance(index, tuple) or len(index) != 2:
            raise IndexError("Index must be tuple")
        if index[0] >= self.width or index[1] >= self.height:
            raise IndexError("Pixel assignment outside available coordinates.")

        offset = self._calculate_pixel_offset(index)

        self._neopixel[offset] = value

    def __getitem__(self, index):
        if not isinstance(index, tuple) or len(index) != 2:
            raise IndexError("Index must be tuple")
        if index[0] >= self.width or index[1] >= self.height:
            raise IndexError("Pixel outside available coordinates.")

        offset = self._calculate_pixel_offset(index)

        return self._neopixel[offset]

    def _calculate_pixel_offset(self, index):
        if self._rotation == 0 or self._rotation == 180:
            offset = self.width * index[1] + index[0]
            if self._rotation == 180:
                offset = self.width * self.height - offset - 1
        elif self._rotation == 270:
            offset = self.height * index[0] + (self.height - index[1] - 1)
        elif self._rotation == 90:
            offset = self.height * (self.width - index[0] - 1) + index[1]

        if offset < 0:
            raise IndexError("Pixel outside available coordinates.")

        return offset

    def show(self):
        """
        Shows the new colors on the pixels themselves if they haven't already
        been autowritten.

        Use when ``auto_write`` is set to ``False``.

        The colors may or may not be showing after this function returns because
        it may be done asynchronously.
        """
        self._neopixel.show()

    @property
    def auto_write(self):
        """
        True if the neopixels should immediately change when set. If False,
        ``show`` must be called explicitly.

        This example disables ``auto_write``, sets every pixel, calls ``show()``, then
        re-enables ``auto-write``.

        .. code-block:: python

            import adafruit_trellism4

            trellis = adafruit_trellism4.TrellisM4Express()

            trellis.pixels.auto_write = False

            for x in range(trellis.pixels.width):
                for y in range(trellis.pixels.height):
                    trellis.pixels[x, y] = (0, 255, 0)

            trellis.pixels.show() # must call show() when auto_write == False

            trellis.pixels.auto_write = True
        """
        return self._neopixel.auto_write

    @auto_write.setter
    def auto_write(self, val):
        self._neopixel.auto_write = val

    @property
    def brightness(self):
        """
        The overall brightness of the pixel. Must be a number between 0 and
        1, where the number represents a percentage between 0 and 100, i.e. ``0.3`` is 30%.

        This example sets the brightness to ``0.3`` and turns all the LEDs red:

        .. code-block:: python

            import adafruit_trellism4

            trellis = adafruit_trellism4.TrellisM4Express()

            trellis.pixels.brightness = 0.3

            trellis.pixels.fill((255, 0, 0))
        """
        return self._neopixel.brightness

    @brightness.setter
    def brightness(self, brightness):
        self._neopixel.brightness = brightness

    def fill(self, color):
        """
        Colors all the pixels a given color.

        :param color: An (R, G, B) color tuple (such as (255, 0, 0) for red), or a hex color value
                      (such as 0xff0000 for red).

        .. code-block:: python

            import adafruit_trellism4

            trellis = adafruit_trellism4.TrellisM4Express()

            trellis.pixels.fill((255, 0, 0))

        """
        self._neopixel.fill(color)

    @property
    def width(self):
        """
        The width of the grid. When ``rotation`` is 0, ``width`` is 8.

        .. code-block:: python

            import adafruit_trellism4

            trellis = adafruit_trellism4.TrellisM4Express()

            for x in range(trellis.pixels.width):
                for y in range(trellis.pixels.height):
                    trellis.pixels[x, y] = (0, 0, 255)
        """
        return self._width

    @property
    def height(self):
        """The height of the grid. When ``rotation`` is 0, ``height`` is 4.

        .. code-block:: python

            import adafruit_trellism4

            trellis = adafruit_trellism4.TrellisM4Express()

            for x in range(trellis.pixels.width):
                for y in range(trellis.pixels.height):
                    trellis.pixels[x, y] = (0, 0, 255)
        """
        return self._height


class TrellisM4Express:
    """
    Represents a single Trellis M4 Express. Do not use more than one at a time.

    :param rotation: Allows for rotating the Trellis M4 Express in 90 degree increments to different
                     positions and utilising the grid from that position. Supports ``0``, ``90``,
                     ``180``, and ``270``. ``0`` degrees is when the USB facing away from you.
                     Default is 0.

    .. code-block:: python

         import time
         import adafruit_trellism4

         trellis = adafruit_trellism4.TrellisM4Express()

         current_press = set()
         while True:
             pressed = set(trellis.pressed_keys)
             for press in pressed - current_press:
                print("Pressed:", press)
            for release in current_press - pressed:
                print("Released:", release)
            time.sleep(0.08)
            current_press = pressed
    """

    def __init__(self, rotation=0):
        self._rotation = rotation

        # Define NeoPixels
        self.pixels = _NeoPixelArray(
            board.NEOPIXEL, width=8, height=4, rotation=rotation
        )
        """Sequence like object representing the 32 NeoPixels on the Trellis M4 Express, Provides a
        two dimensional representation of the NeoPixel grid.

        This example lights up the first pixel green:

        .. code-block:: python

            import adafruit_trellism4

            trellis = adafruit_trellism4.TrellisM4Express()

            trellis.pixels[0, 0] = (0, 255, 0)

        **Options for** ``pixels``:

        ``pixels.fill``: Colors all the pixels a given color. Provide an (R, G, B) color tuple
        (such as (255, 0, 0) for red), or a hex color value (such as 0xff0000 for red).

            This example colors all pixels red:

            .. code-block:: python

                import adafruit_trellism4

                trellis = adafruit_trellism4.TrellisM4Express()

                trellis.pixels.fill((255, 0, 0))

        ``pixels.width`` and ``pixels.height``: The width and height of the grid. When ``rotation``
        is 0, ``width`` is 8 and ``height`` is 4.

            This example colors all pixels blue:

            .. code-block:: python

                import adafruit_trellism4

                trellis = adafruit_trellism4.TrellisM4Express()

                for x in range(trellis.pixels.width):
                    for y in range(trellis.pixels.height):
                        trellis.pixels[x, y] = (0, 0, 255)

        ``pixels.brightness``: The overall brightness of the pixel. Must be a number between 0 and
        1, where the number represents a percentage between 0 and 100, i.e. ``0.3`` is 30%.

            This example sets the brightness to ``0.3`` and turns all the LEDs red:

            .. code-block:: python

                import adafruit_trellism4

                trellis = adafruit_trellism4.TrellisM4Express()

                trellis.pixels.brightness = 0.3

                trellis.pixels.fill((255, 0, 0))
        """

        cols = []
        for x in range(8):
            col = digitalio.DigitalInOut(getattr(board, "COL{}".format(x)))
            cols.append(col)

        rows = []
        for y in range(4):
            row = digitalio.DigitalInOut(getattr(board, "ROW{}".format(y)))
            rows.append(row)

        key_names = []
        for y in range(8):
            row = []
            for x in range(4):
                if rotation == 0:
                    coord = (y, x)
                elif rotation == 180:
                    coord = (7 - y, 3 - x)
                elif rotation == 90:
                    coord = (3 - x, y)
                elif rotation == 270:
                    coord = (x, 7 - y)
                row.append(coord)
            key_names.append(row)

        self._matrix = adafruit_matrixkeypad.Matrix_Keypad(cols, rows, key_names)

    @property
    def pressed_keys(self):
        """A list of tuples of currently pressed button coordinates.

        .. code-block:: python

            import time
            import adafruit_trellism4

            trellis = adafruit_trellism4.TrellisM4Express()

            current_press = set()
            while True:
                pressed = set(trellis.pressed_keys)
                for press in pressed - current_press:
                    print("Pressed:", press)
                for release in current_press - pressed:
                    print("Released:", release)
                time.sleep(0.08)
                current_press = pressed
        """
        return self._matrix.pressed_keys
