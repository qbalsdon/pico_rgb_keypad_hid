# SPDX-FileCopyrightText: 2019 Melissa LeBlanc-Williams for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_featherwing.pixelmatrix`
====================================================

Base Class for the `NeoPixel FeatherWing <https://www.adafruit.com/product/2945>` and
`DotStar FeatherWing <https://www.adafruit.com/product/3449>`_.

* Author(s): Melissa LeBlanc-Williams
"""

__version__ = "1.13.3"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_FeatherWing.git"

# pylint: disable-msg=unsubscriptable-object, unsupported-assignment-operation


class PixelMatrix:
    """Base Class for DotStar and NeoPixel FeatherWings

    The feather uses pins D13 and D11"""

    def __init__(self):
        self.rows = 0
        self.columns = 0
        self._matrix = None
        self._auto_write = True

    def __setitem__(self, indices, value):
        """
        indices can be one of three things:
            x and y ints that are calculated to the DotStar index
            a slice of DotStar indexes with a set of values that match the slice
            a single int that specifies the DotStar index
        value can be one of three things:
                a (r,g,b) list/tuple
                a (r,g,b, brightness) list/tuple
                a single, longer int that contains RGB values, like 0xFFFFFF
            brightness, if specified should be a float 0-1
        """
        self._matrix[self._get_index(indices)] = value
        self._update()

    def __getitem__(self, indices):
        """
        indices can be one of three things:
            x and y ints that are calculated to the DotStar index
            a slice of DotStar indexes to retrieve
            a single int that specifies the DotStar index
        """
        return self._matrix[self._get_index(indices)]

    def _get_index(self, indices):
        """
        Figure out which DotStar to address based on what was passed in
        """
        if isinstance(indices, int):
            if not 0 <= indices < self.rows * self.columns:
                raise ValueError("The index of {} is out of range".format(indices))
            return indices
        if isinstance(indices, slice):
            return indices
        if len(indices) == 2:
            x, y = indices
            if not 0 <= x < self.columns:
                raise ValueError("The X value of {} is out of range".format(x))
            if not 0 <= y < self.rows:
                raise ValueError("The Y value of {} is out of range".format(y))
            return y * self.columns + x
        raise ValueError("Index must be 1 or 2 number")

    def _update(self):
        """
        Update the Display automatically if auto_write is set to True
        """
        if self._auto_write:
            self._matrix.show()

    def fill(self, color=0):
        """
        Fills all of the Pixels with a color or unlit if empty.

        :param color: (Optional) The text or number to display (default=0)
        :type color: list/tuple or int
        """
        self._matrix.fill(color)
        self._update()

    def show(self):
        """
        Update the Pixels. This is only needed if auto_write is set to False
        This can be very useful for more advanced graphics effects.
        """
        self._matrix.show()

    def shift_right(self, rotate=False):
        """
        Shift all pixels right

        :param rotate: (Optional) Rotate the shifted pixels to the left side (default=False)
        """
        for y in range(0, self.rows):
            last_pixel = self._matrix[(y + 1) * self.columns - 1] if rotate else 0
            for x in range(self.columns - 1, 0, -1):
                self._matrix[y * self.columns + x] = self._matrix[
                    y * self.columns + x - 1
                ]
            self._matrix[y * self.columns] = last_pixel
        self._update()

    def shift_left(self, rotate=False):
        """
        Shift all pixels left

        :param rotate: (Optional) Rotate the shifted pixels to the right side (default=False)
        """
        for y in range(0, self.rows):
            last_pixel = self._matrix[y * self.columns] if rotate else 0
            for x in range(0, self.columns - 1):
                self._matrix[y * self.columns + x] = self._matrix[
                    y * self.columns + x + 1
                ]
            self._matrix[(y + 1) * self.columns - 1] = last_pixel
        self._update()

    def shift_up(self, rotate=False):
        """
        Shift all pixels up

        :param rotate: (Optional) Rotate the shifted pixels to bottom (default=False)
        """
        for x in range(0, self.columns):
            last_pixel = (
                self._matrix[(self.rows - 1) * self.columns + x] if rotate else 0
            )
            for y in range(self.rows - 1, 0, -1):
                self._matrix[y * self.columns + x] = self._matrix[
                    (y - 1) * self.columns + x
                ]
            self._matrix[x] = last_pixel
        self._update()

    def shift_down(self, rotate=False):
        """
        Shift all pixels down

        :param rotate: (Optional) Rotate the shifted pixels to top (default=False)
        """
        for x in range(0, self.columns):
            last_pixel = self._matrix[x] if rotate else 0
            for y in range(0, self.rows - 1):
                self._matrix[y * self.columns + x] = self._matrix[
                    (y + 1) * self.columns + x
                ]
            self._matrix[(self.rows - 1) * self.columns + x] = last_pixel
        self._update()

    @property
    def auto_write(self):
        """
        Whether or not we are automatically updating
        If set to false, be sure to call show() to update
        """
        return self._auto_write

    @auto_write.setter
    def auto_write(self, write):
        if isinstance(write, bool):
            self._auto_write = write

    @property
    def brightness(self):
        """
        Overall brightness of the display
        """
        return self._matrix.brightness

    @brightness.setter
    def brightness(self, brightness):
        self._matrix.brightness = min(max(brightness, 0.0), 1.0)
        self._update()
