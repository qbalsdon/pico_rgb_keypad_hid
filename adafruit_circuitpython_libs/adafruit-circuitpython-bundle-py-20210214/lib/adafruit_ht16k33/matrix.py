# SPDX-FileCopyrightText: Radomir Dopieralski 2016 for Adafruit Industries
# SPDX-FileCopyrightText: Tony DiCola 2016 for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
Matrix Displays
================

"""
from adafruit_ht16k33.ht16k33 import HT16K33

__version__ = "4.1.3"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_HT16K33.git"


class Matrix8x8(HT16K33):
    """A single matrix."""

    _columns = 8
    _rows = 8

    def pixel(self, x, y, color=None):
        """Get or set the color of a given pixel."""
        if not 0 <= x <= 7:
            return None
        if not 0 <= y <= 7:
            return None
        x = (x - 1) % 8
        return super()._pixel(x, y, color)

    def __getitem__(self, key):
        x, y = key
        return self.pixel(x, y)

    def __setitem__(self, key, value):
        x, y = key
        self.pixel(x, y, value)

    # pylint: disable=too-many-branches
    def shift(self, x, y, rotate=False):
        """
        Shift pixels by x and y

        :param rotate: (Optional) Rotate the shifted pixels to the left side (default=False)
        """
        auto_write = self.auto_write
        self._auto_write = False
        if x > 0:  # Shift Right
            for _ in range(x):
                for row in range(0, self.rows):
                    last_pixel = self[self.columns - 1, row] if rotate else 0
                    for col in range(self.columns - 1, 0, -1):
                        self[col, row] = self[col - 1, row]
                    self[0, row] = last_pixel
        elif x < 0:  # Shift Left
            for _ in range(-x):
                for row in range(0, self.rows):
                    last_pixel = self[0, row] if rotate else 0
                    for col in range(0, self.columns - 1):
                        self[col, row] = self[col + 1, row]
                    self[self.columns - 1, row] = last_pixel
        if y > 0:  # Shift Up
            for _ in range(y):
                for col in range(0, self.columns):
                    last_pixel = self[col, self.rows - 1] if rotate else 0
                    for row in range(self.rows - 1, 0, -1):
                        self[col, row] = self[col, row - 1]
                    self[col, 0] = last_pixel
        elif y < 0:  # Shift Down
            for _ in range(-y):
                for col in range(0, self.columns):
                    last_pixel = self[col, 0] if rotate else 0
                    for row in range(0, self.rows - 1):
                        self[col, row] = self[col, row + 1]
                    self[col, self.rows - 1] = last_pixel
        self._auto_write = auto_write
        if auto_write:
            self.show()

    # pylint: enable=too-many-branches

    def shift_right(self, rotate=False):
        """
        Shift all pixels right

        :param rotate: (Optional) Rotate the shifted pixels to the left side (default=False)
        """
        self.shift(1, 0, rotate)

    def shift_left(self, rotate=False):
        """
        Shift all pixels left

        :param rotate: (Optional) Rotate the shifted pixels to the right side (default=False)
        """
        self.shift(-1, 0, rotate)

    def shift_up(self, rotate=False):
        """
        Shift all pixels up

        :param rotate: (Optional) Rotate the shifted pixels to bottom (default=False)
        """
        self.shift(0, 1, rotate)

    def shift_down(self, rotate=False):
        """
        Shift all pixels down

        :param rotate: (Optional) Rotate the shifted pixels to top (default=False)
        """
        self.shift(0, -1, rotate)

    def image(self, img):
        """Set buffer to value of Python Imaging Library image.  The image should
        be in 1 bit mode and a size equal to the display size."""
        imwidth, imheight = img.size
        if imwidth != self.columns or imheight != self.rows:
            raise ValueError(
                "Image must be same dimensions as display ({0}x{1}).".format(
                    self.columns, self.rows
                )
            )
        # Grab all the pixels from the image, faster than getpixel.
        pixels = img.convert("1").load()
        # Iterate through the pixels
        for x in range(self.columns):  # yes this double loop is slow,
            for y in range(self.rows):  #  but these displays are small!
                self.pixel(x, y, pixels[(x, y)])
        if self._auto_write:
            self.show()

    @property
    def columns(self):
        """Read-only property for number of columns"""
        return self._columns

    @property
    def rows(self):
        """Read-only property for number of rows"""
        return self._rows


class Matrix16x8(Matrix8x8):
    """The matrix wing."""

    _columns = 16

    def pixel(self, x, y, color=None):
        """Get or set the color of a given pixel."""
        if not 0 <= x <= 15:
            return None
        if not 0 <= y <= 7:
            return None
        if x >= 8:
            x -= 8
            y += 8
        return super()._pixel(y, x, color)  # pylint: disable=arguments-out-of-order


class MatrixBackpack16x8(Matrix16x8):
    """A double matrix backpack."""

    def pixel(self, x, y, color=None):
        """Get or set the color of a given pixel."""
        if not 0 <= x <= 15:
            return None
        if not 0 <= y <= 7:
            return None
        return super()._pixel(x, y, color)


class Matrix8x8x2(Matrix8x8):
    """A bi-color matrix."""

    LED_OFF = 0
    LED_RED = 1
    LED_GREEN = 2
    LED_YELLOW = 3

    def pixel(self, x, y, color=None):
        """Get or set the color of a given pixel."""
        if not 0 <= x <= 7:
            return None
        if not 0 <= y <= 7:
            return None
        if color is not None:
            super()._pixel(y, x, (color >> 1) & 0x01)
            super()._pixel(y + 8, x, (color & 0x01))
        else:
            return super()._pixel(y, x) | super()._pixel(y + 8, x) << 1
        return None

    def fill(self, color):
        """Fill the whole display with the given color."""
        fill1 = 0xFF if color & 0x01 else 0x00
        fill2 = 0xFF if color & 0x02 else 0x00
        for i in range(8):
            self._set_buffer(i * 2, fill1)
            self._set_buffer(i * 2 + 1, fill2)
        if self._auto_write:
            self.show()

    def image(self, img):
        """Set buffer to value of Python Imaging Library image.  The image should
        be a size equal to the display size."""
        imwidth, imheight = img.size
        if imwidth != self.columns or imheight != self.rows:
            raise ValueError(
                "Image must be same dimensions as display ({0}x{1}).".format(
                    self.columns, self.rows
                )
            )
        # Grab all the pixels from the image, faster than getpixel.
        pixels = img.convert("RGB").load()
        # Iterate through the pixels
        for x in range(self.columns):  # yes this double loop is slow,
            for y in range(self.rows):  #  but these displays are small!
                if pixels[(x, y)] == (255, 0, 0):
                    self.pixel(x, y, self.LED_RED)
                elif pixels[(x, y)] == (0, 255, 0):
                    self.pixel(x, y, self.LED_GREEN)
                elif pixels[(x, y)] == (255, 255, 0):
                    self.pixel(x, y, self.LED_YELLOW)
                else:
                    # Unknown color, default to LED off.
                    self.pixel(x, y, self.LED_OFF)
        if self._auto_write:
            self.show()
