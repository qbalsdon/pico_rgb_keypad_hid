# SPDX-FileCopyrightText: 2019 Brent Rubell for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_cursorcontrol`
================================================================================

Mouse cursor for interaction with CircuitPython UI elements.


* Author(s): Brent Rubell

Implementation Notes
--------------------

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://github.com/adafruit/circuitpython/releases

"""
import displayio

__version__ = "2.2.4"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_Cursor.git"


class Cursor:
    """Mouse cursor interaction for CircuitPython.

    :param ~displayio.Display display: CircuitPython display object.
    :param ~displayio.Group display_group: CircuitPython group object to append the cursor to.
    :param int cursor_speed: Speed of the cursor, in pixels.
    :param int scale: Scale amount for the cursor in both directions.
    :param bool is_hidden: Cursor is hidden on init.

    Example for creating a cursor layer

    .. code-block:: python

        from adafruit_cursorcontrol import Cursor
        # Create the display
        display = board.DISPLAY

        # Create the display context
        splash = displayio.Group(max_size=22)

        # initialize the mouse cursor object
        mouse_cursor = Cursor(display, display_group=splash)
    """

    # pylint: disable=too-many-arguments,line-too-long
    def __init__(
        self,
        display=None,
        display_group=None,
        bmp=None,
        is_hidden=False,
        cursor_speed=5,
        scale=1,
    ):
        self._display = display
        self._scale = scale
        self._speed = cursor_speed
        self._is_hidden = is_hidden
        self._display_grp = display_group
        self._disp_sz = display.height - 1, display.width - 1
        self._cur_sprite = None
        if bmp is None:
            self._cursor_bitmap = self._default_cursor_bitmap()
        else:
            self._cursor_bitmap = bmp
        self.generate_cursor(self._cursor_bitmap)

    # pylint: enable=too-many-arguments,line-too-long

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        self.deinit()

    def deinit(self):
        """deinitializes the cursor object."""
        self._is_deinited()
        self._scale = None
        self._display_grp.remove(self._cursor_grp)

    def _is_deinited(self):
        """checks cursor deinitialization"""
        if self._scale is None:
            raise ValueError(
                "Cursor object has been deinitialized and can no longer "
                "be used. Create a new cursor object."
            )

    @property
    def scale(self):
        """Returns the cursor's scale amount as an integer."""
        return self._scale

    @scale.setter
    def scale(self, scale_value):
        """Scales the cursor by scale_value in both directions.
        :param int scale_value: Amount to scale the cursor by.
        """
        self._is_deinited()
        if scale_value > 0:
            self._scale = scale_value
            self._cursor_grp.scale = scale_value

    @property
    def speed(self):
        """Returns the cursor's speed, in pixels."""
        return self._speed

    @speed.setter
    def speed(self, speed):
        """Sets the speed of the cursor.
        :param int speed: Cursor movement speed, in pixels.
        """
        self._is_deinited()
        if speed > 0:
            self._speed = speed

    @property
    def x(self):
        """Returns the cursor's x-coordinate."""
        return self._cursor_grp.x

    @x.setter
    def x(self, x_val):
        """Sets the x-value of the cursor.
        :param int x_val: cursor x-position, in pixels.
        """
        self._is_deinited()
        if x_val < 0 and not self._is_hidden:
            self._cursor_grp.x = self._cursor_grp.x
        elif x_val > self._disp_sz[1] and not self._is_hidden:
            self._cursor_grp.x = self._cursor_grp.x
        elif not self._is_hidden:
            self._cursor_grp.x = x_val

    @property
    def y(self):
        """Returns the cursor's y-coordinate."""
        return self._cursor_grp.y

    @y.setter
    def y(self, y_val):
        """Sets the y-value of the cursor.
        :param int y_val: cursor y-position, in pixels.
        """
        self._is_deinited()
        if y_val < 0 and not self._is_hidden:
            self._cursor_grp.y = self._cursor_grp.y
        elif y_val > self._disp_sz[0] and not self._is_hidden:
            self._cursor_grp.y = self._cursor_grp.y
        elif not self._is_hidden:
            self._cursor_grp.y = y_val

    @property
    def hidden(self):
        """Returns True if the cursor is hidden or visible on the display."""
        return self._is_hidden

    @hidden.setter
    def hidden(self, is_hidden):
        self._is_deinited()
        if is_hidden:
            self._is_hidden = True
            self._display_grp.remove(self._cursor_grp)
        else:
            self._is_hidden = False
            self._display_grp.append(self._cursor_grp)

    def hide(self):
        """Hide the cursor."""
        self.hidden = True

    def show(self):
        """Show the cursor."""
        self.hidden = False

    # pylint:disable=no-self-use
    def _default_cursor_bitmap(self):
        bmp = displayio.Bitmap(20, 20, 3)
        # left edge, outline
        for i in range(0, bmp.height):
            bmp[0, i] = 2
        # right diag outline, inside fill
        for j in range(1, 15):
            bmp[j, j] = 2
            for i in range(j + 1, bmp.height - j):
                bmp[j, i] = 1
        # bottom diag., outline
        for i in range(1, 5):
            bmp[i, bmp.height - i] = 2
        # bottom flat line, right side fill
        for i in range(5, 15):
            bmp[i, 15] = 2
            bmp[i - 1, 14] = 1
            bmp[i - 2, 13] = 1
            bmp[i - 3, 12] = 1
            bmp[i - 4, 11] = 1
        return bmp

    # pylint:enable=no-self-use

    @property
    def cursor_bitmap(self):
        """Return the cursor bitmap."""
        return self._cursor_bitmap

    @cursor_bitmap.setter
    def cursor_bitmap(self, bmp):
        """Set a new cursor bitmap.

        :param bmp: A Bitmap to use for the cursor
        """
        self._cursor_bitmap = bmp
        self._cursor_grp.remove(self._cur_sprite)
        self._cur_sprite = displayio.TileGrid(bmp, pixel_shader=self._cur_palette)
        self._cursor_grp.append(self._cur_sprite)

    def generate_cursor(self, bmp):
        """Generates a cursor icon"""
        self._is_deinited()
        self._cursor_grp = displayio.Group(max_size=1, scale=self._scale)
        self._cur_palette = displayio.Palette(3)
        self._cur_palette.make_transparent(0)
        self._cur_palette[1] = 0xFFFFFF
        self._cur_palette[2] = 0x0000
        self._cur_sprite = displayio.TileGrid(bmp, pixel_shader=self._cur_palette)
        self._cursor_grp.append(self._cur_sprite)
        self._display_grp.append(self._cursor_grp)
