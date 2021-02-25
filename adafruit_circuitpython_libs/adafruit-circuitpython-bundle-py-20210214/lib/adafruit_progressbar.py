# SPDX-FileCopyrightText: 2020 Brent Rubell for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_progressbar`
================================================================================

Dynamic progress bar widget for CircuitPython displays


* Author(s): Brent Rubell

Implementation Notes
--------------------

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://github.com/adafruit/circuitpython/releases

"""

# imports
import displayio

__version__ = "1.3.7"
__repo__ = "https://github.com/brentru/Adafruit_CircuitPython_ProgressBar.git"

# pylint: disable=too-many-arguments, too-few-public-methods
class ProgressBar(displayio.TileGrid):
    """A dynamic progress bar widget.

    :param int x: The x-position of the top left corner.
    :param int y: The y-position of the top left corner.
    :param int width: The width of the progress bar.
    :param int height: The height of the progress bar.
    :param float progress: The percentage of the progress bar.
    :param bar_color: The color of the progress bar. Can be a hex
                                value for color.
    :param int outline_color: The outline of the progress bar. Can be a hex
                            value for color.
    :param int stroke: Used for the outline_color

    """

    # pylint: disable=invalid-name
    def __init__(
        self,
        x,
        y,
        width,
        height,
        progress=0.0,
        bar_color=0x00FF00,
        outline_color=0xFFFFFF,
        stroke=1,
    ):
        assert isinstance(progress, float), "Progress must be a floating point value."
        self._bitmap = displayio.Bitmap(width, height, 3)
        self._palette = displayio.Palette(3)
        self._palette[0] = 0x0
        self._palette[1] = outline_color
        self._palette[2] = bar_color

        # _width and _height are already in use for blinka TileGrid
        self._bar_width = width
        self._bar_height = height

        self._progress_val = 0.0
        self.progress = self._progress_val
        self.progress = progress

        # draw outline rectangle
        for _w in range(width):
            for line in range(stroke):
                self._bitmap[_w, line] = 1
                self._bitmap[_w, height - 1 - line] = 1
        for _h in range(height):
            for line in range(stroke):
                self._bitmap[line, _h] = 1
                self._bitmap[width - 1 - line, _h] = 1
        super().__init__(self._bitmap, pixel_shader=self._palette, x=x, y=y)

    @property
    def progress(self):
        """The percentage of the progress bar expressed as a
        floating point number.

        """
        return self._progress_val

    @progress.setter
    def progress(self, value):
        """Draws the progress bar

        :param float value: Progress bar value.
        """
        assert value <= 1.0, "Progress value may not be > 100%"
        assert isinstance(
            value, float
        ), "Progress value must be a floating point value."
        if self._progress_val > value:
            # uncolorize range from width*value+margin to width-margin
            # from right to left
            _prev_pixel = max(2, int(self.width * self._progress_val - 2))
            _new_pixel = max(int(self.width * value - 2), 2)
            for _w in range(_prev_pixel, _new_pixel - 1, -1):
                for _h in range(2, self.height - 2):
                    self._bitmap[_w, _h] = 0
        else:
            # fill from the previous x pixel to the new x pixel
            _prev_pixel = max(2, int(self.width * self._progress_val - 3))
            _new_pixel = min(int(self.width * value - 2), int(self.width * 1.0 - 3))
            for _w in range(_prev_pixel, _new_pixel + 1):
                for _h in range(2, self.height - 2):
                    self._bitmap[_w, _h] = 2
        self._progress_val = value

    @property
    def fill(self):
        """The fill of the progress bar. Can be a hex value for a color or ``None`` for
        transparent.

        """
        return self._palette[0]

    @property
    def width(self):
        """The width of the progress bar. In pixels, includes the border."""
        return self._bar_width

    @property
    def height(self):
        """The height of the progress bar. In pixels, includes the border."""
        return self._bar_height

    @fill.setter
    def fill(self, color):
        """Sets the fill of the progress bar. Can be a hex value for a color or ``None`` for
        transparent.

        """
        if color is None:
            self._palette[2] = 0
            self._palette.make_transparent(0)
        else:
            self._palette[2] = color
            self._palette.make_opaque(0)
