# SPDX-FileCopyrightText: 2006-2010 Gregor Lingl for Adafruit Industries
# SPDX-FileCopyrightText: 2019 LadyAda for Adafruit Industries
# SPDX-FileCopyrightText: 2021 Dave Astels for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_turtle`
================================================================================

* Originals Author(s): LadyAda and Dave Astels

Implementation Notes
--------------------

**Hardware:**

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://github.com/adafruit/circuitpython/releases

* Adafruit's Bus Device library:
  https://github.com/adafruit/Adafruit_CircuitPython_BusDevice
"""

# pylint:disable=too-many-public-methods, too-many-instance-attributes, invalid-name
# pylint:disable=too-few-public-methods, too-many-lines, too-many-arguments

import gc
import math
import time
import board
import displayio

__version__ = "2.1.4"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_turtle.git"


class Color:
    """Standard colors"""

    WHITE = 0xFFFFFF
    BLACK = 0x000000
    RED = 0xFF0000
    ORANGE = 0xFFA500
    YELLOW = 0xFFEE00
    GREEN = 0x00C000
    BLUE = 0x0000FF
    PURPLE = 0x8040C0
    PINK = 0xFF40C0
    LIGHT_GRAY = 0xAAAAAA
    GRAY = 0x444444
    BROWN = 0xCA801D
    DARK_GREEN = 0x008700
    TURQUOISE = 0x00C0C0
    DARK_BLUE = 0x0000AA
    DARK_RED = 0x800000

    colors = (
        BLACK,
        WHITE,
        RED,
        YELLOW,
        GREEN,
        ORANGE,
        BLUE,
        PURPLE,
        PINK,
        GRAY,
        LIGHT_GRAY,
        BROWN,
        DARK_GREEN,
        TURQUOISE,
        DARK_BLUE,
        DARK_RED,
    )

    def __init__(self):
        pass


class Vec2D(tuple):
    """A 2 dimensional vector class, used as a helper class
    for implementing turtle graphics.
    May be useful for turtle graphics programs also.
    Derived from tuple, so a vector is a tuple!
    """

    # Provides (for a, b vectors, k number):
    #     a+b vector addition
    #     a-b vector subtraction
    #     a*b inner product
    #     k*a and a*k multiplication with scalar
    #     |a| absolute value of a
    #     a.rotate(angle) rotation
    def __init__(self, x, y):
        super().__init__((x, y))

    def __add__(self, other):
        return Vec2D(self[0] + other[0], self[1] + other[1])

    def __mul__(self, other):
        if isinstance(other, Vec2D):
            return self[0] * other[0] + self[1] * other[1]
        return Vec2D(self[0] * other, self[1] * other)

    def __rmul__(self, other):
        if isinstance(other, (float, int)):
            return Vec2D(self[0] * other, self[1] * other)
        return None

    def __sub__(self, other):
        return Vec2D(self[0] - other[0], self[1] - other[1])

    def __neg__(self):
        return Vec2D(-self[0], -self[1])

    def __abs__(self):
        return (self[0] ** 2 + self[1] ** 2) ** 0.5

    def rotate(self, angle):
        """Rotate self counterclockwise by angle.

        :param angle: how much to rotate

        """
        perp = Vec2D(-self[1], self[0])
        angle = angle * math.pi / 180.0
        c, s = math.cos(angle), math.sin(angle)
        return Vec2D(self[0] * c + perp[0] * s, self[1] * c + perp[1] * s)

    def __getnewargs__(self):
        return (self[0], self[1])

    def __repr__(self):
        return "({:.2f},{:.2f})".format(self[0], self[1])


class turtle:
    """A Turtle that can be given commands to draw."""

    # pylint:disable=too-many-statements
    def __init__(self, display=None, scale=1):

        if display:
            self._display = display
        else:
            try:
                self._display = board.DISPLAY
            except AttributeError as err:
                raise RuntimeError(
                    "No display available. One must be provided."
                ) from err

        self._w = self._display.width
        self._h = self._display.height
        self._x = self._w // (2 * scale)
        self._y = self._h // (2 * scale)
        self._speed = 6
        self._heading = 0
        self._logomode = True
        self._fullcircle = 360.0
        self._degreesPerAU = 1.0
        self._angleOrient = 1
        self._angleOffset = 0
        self._bg_color = 0

        self._splash = displayio.Group(max_size=5)
        self._bgscale = 1
        if self._w == self._h:
            i = 1
            while self._bgscale == 1:
                if self._w / i < 128:
                    self._bg_bitmap = displayio.Bitmap(i, i, 1)
                    self._bgscale = self._w // i
                i += 1
        else:
            self._bgscale = self._GCD(self._w, self._h)
            self._bg_bitmap = displayio.Bitmap(
                self._w // self._bgscale, self._h // self._bgscale, 1
            )
        self._bg_palette = displayio.Palette(1)
        self._bg_palette[0] = Color.colors[self._bg_color]
        self._bg_sprite = displayio.TileGrid(
            self._bg_bitmap, pixel_shader=self._bg_palette, x=0, y=0
        )
        self._bg_group = displayio.Group(scale=self._bgscale, max_size=1)
        self._bg_group.append(self._bg_sprite)
        self._splash.append(self._bg_group)
        # group to add background pictures (and/or user-defined stuff)
        self._bg_addon_group = displayio.Group(max_size=6)
        self._splash.append(self._bg_addon_group)
        self._fg_scale = scale
        self._w = self._w // self._fg_scale
        self._h = self._h // self._fg_scale
        self._fg_bitmap = displayio.Bitmap(self._w, self._h, len(Color.colors))

        self._fg_palette = displayio.Palette(len(Color.colors))
        self._fg_palette.make_transparent(self._bg_color)
        for i, c in enumerate(Color.colors):
            self._fg_palette[i] = c
        self._fg_sprite = displayio.TileGrid(
            self._fg_bitmap, pixel_shader=self._fg_palette, x=0, y=0
        )
        self._fg_group = displayio.Group(scale=self._fg_scale, max_size=1)
        self._fg_group.append(self._fg_sprite)
        self._splash.append(self._fg_group)
        # group to add text and/or user defined stuff
        self._fg_addon_group = displayio.Group(max_size=6)
        self._splash.append(self._fg_addon_group)

        self._turtle_bitmap = displayio.Bitmap(9, 9, 2)
        self._turtle_palette = displayio.Palette(2)
        self._turtle_palette.make_transparent(0)

        self._turtle_palette[1] = Color.WHITE
        for i in range(4):
            self._turtle_bitmap[4 - i, i] = 1
            self._turtle_bitmap[i, 4 + i] = 1
            self._turtle_bitmap[4 + i, 7 - i] = 1
            self._turtle_bitmap[4 + i, i] = 1
        self._turtle_sprite = displayio.TileGrid(
            self._turtle_bitmap, pixel_shader=self._turtle_palette, x=-100, y=-100
        )

        self._turtle_group = displayio.Group(scale=self._fg_scale, max_size=2)
        self._turtle_group.append(self._turtle_sprite)
        self._splash.append(self._turtle_group)
        self._penstate = False
        self._pensize = 1
        self._pencolor = 1
        self.pencolor(Color.WHITE)
        self._bg_pic = None
        self._bg_pic_filename = ""
        self._turtle_pic = None
        self._turtle_odb = None
        self._turtle_alt_sprite = None
        self._drawturtle()
        self._stamps = {}
        self._turtle_odb_use = 0
        self._turtle_odb_file = None
        self._odb_tilegrid = None
        gc.collect()
        self._display.show(self._splash)

    # pylint:enable=too-many-statements

    def _drawturtle(self):
        if self._turtle_pic is None:
            self._turtle_sprite.x = int(self._x - 4)
            self._turtle_sprite.y = int(self._y - 4)
        else:
            if self._turtle_odb is not None:
                self._turtle_alt_sprite.x = int(self._x - self._turtle_odb.width // 2)
                self._turtle_alt_sprite.y = int(self._y - self._turtle_odb.height // 2)
            else:
                self._turtle_alt_sprite.x = int(self._x - self._turtle_pic[0] // 2)
                self._turtle_alt_sprite.y = int(self._y - self._turtle_pic[1] // 2)

    ###########################################################################
    # Move and draw

    def forward(self, distance):
        """Move the turtle forward by the specified distance, in the direction the turtle is headed.

        :param distance: how far to move (integer or float)
        """
        p = self.pos()
        angle = (
            self._angleOffset + self._angleOrient * self._heading
        ) % self._fullcircle
        x1 = p[0] + math.sin(math.radians(angle)) * distance
        y1 = p[1] + math.cos(math.radians(angle)) * distance
        self.goto(x1, y1)

    fd = forward

    def backward(self, distance):
        """Move the turtle backward by distance, opposite to the direction the turtle is headed.
        Does not change the turtle's heading.

        :param distance: how far to move (integer or float)
        """

        self.forward(-distance)

    bk = backward
    back = backward

    def right(self, angle):
        """Turn turtle right by angle units. (Units are by default degrees,
        but can be set via the degrees() and radians() functions.)
        Angle orientation depends on the turtle mode, see mode().

        :param angle: how much to rotate to the right (integer or float)
        """
        if self._logomode:
            self._turn(angle)
        else:
            self._turn(-angle)

    rt = right

    def left(self, angle):
        """Turn turtle left by angle units. (Units are by default degrees,
        but can be set via the degrees() and radians() functions.)
        Angle orientation depends on the turtle mode, see mode().

        :param angle: how much to rotate to the left (integer or float)
        """
        if self._logomode:
            self._turn(-angle)
        else:
            self._turn(angle)

    lt = left

    # pylint:disable=too-many-branches,too-many-statements
    def goto(self, x1, y1=None):
        """If y1 is None, x1 must be a pair of coordinates or an (x, y) tuple

        Move turtle to an absolute position. If the pen is down, draw line.
        Does not change the turtle's orientation.

        :param x1: a number or a pair of numbers
        :param y1: a number or None
        """
        if y1 is None:
            y1 = x1[1]
            x1 = x1[0]
        x1 += self._w // 2
        y1 = self._h // 2 - y1
        x0 = self._x
        y0 = self._y
        if not self.isdown():
            self._x = x1  # woot, we just skip ahead
            self._y = y1
            self._drawturtle()
            return
        steep = abs(y1 - y0) > abs(x1 - x0)
        rev = False
        dx = x1 - x0

        if steep:
            x0, y0 = y0, x0
            x1, y1 = y1, x1
            dx = x1 - x0

        if x0 > x1:
            rev = True
            dx = x0 - x1

        dy = abs(y1 - y0)
        err = dx / 2
        ystep = -1
        if y0 < y1:
            ystep = 1
        step = 1
        if self._speed > 0:
            ts = ((11 - self._speed) * 0.00020) * (self._speed + 0.5)
        else:
            ts = 0

        while (not rev and x0 <= x1) or (rev and x1 <= x0):
            if steep:
                try:
                    self._plot(int(y0), int(x0), self._pencolor)
                except IndexError:
                    pass
                self._x = y0
                self._y = x0
            else:
                try:
                    self._plot(int(x0), int(y0), self._pencolor)
                except IndexError:
                    pass
                self._x = x0
                self._y = y0
            if self._speed > 0:
                if step >= self._speed:
                    # mark the step
                    step = 1
                    self._drawturtle()
                    time.sleep(ts)
                else:
                    step += 1
            err -= dy
            if err < 0:
                y0 += ystep
                err += dx
            if rev:
                x0 -= 1
            else:
                x0 += 1
        self._drawturtle()

    setpos = goto
    setposition = goto
    # pylint:enable=too-many-branches,too-many-statements

    def setx(self, x):
        """Set the turtle's first coordinate to x, leave second coordinate
        unchanged.

        :param x: new value of the turtle's x coordinate (a number)

        """
        self.goto(x, self.pos()[1])

    def sety(self, y):
        """Set the turtle's second coordinate to y, leave first coordinate
        unchanged.

        :param y: new value of the turtle's y coordinate (a number)

        """
        self.goto(self.pos()[0], y)

    def setheading(self, to_angle):
        """Set the orientation of the turtle to to_angle. Here are some common
        directions in degrees:

        standard mode | logo mode
        0 - east | 0 - north
        90 - north | 90 - east
        180 - west | 180 - south
        270 - south | 270 - west

        :param to_angle: the new turtle heading

        """
        self._turn(to_angle - self._heading)

    seth = setheading

    def home(self):
        """Move turtle to the origin - coordinates (0,0) - and set its heading
        to its start-orientation
        (which depends on the mode, see mode()).
        """
        self.setheading(90)
        self.goto(0, 0)

    # pylint:disable=too-many-locals, too-many-statements, too-many-branches
    def _plot(self, x, y, c):
        if self._pensize == 1:
            try:
                self._fg_bitmap[int(x), int(y)] = c
                return
            except IndexError:
                pass
        r = self._pensize // 2 + 1
        angle = (
            self._angleOffset + self._angleOrient * self._heading - 90
        ) % self._fullcircle
        sin = math.sin(math.radians(angle))
        cos = math.cos(math.radians(angle))
        x0 = x + sin * r
        x1 = x - sin * (self._pensize - r)
        y0 = y - cos * r
        y1 = y + cos * (self._pensize - r)

        coords = [x0, x1, y0, y1]
        for i, v in enumerate(coords):
            if v >= 0:
                coords[i] = math.ceil(v)
            else:
                coords[i] = math.floor(v)
        x0, x1, y0, y1 = coords

        steep = abs(y1 - y0) > abs(x1 - x0)
        rev = False
        dx = x1 - x0
        if steep:
            x0, y0 = y0, x0
            x1, y1 = y1, x1
            dx = x1 - x0

        if x0 > x1:
            rev = True
            dx = x0 - x1

        dy = abs(y1 - y0)
        err = dx / 2
        ystep = -1
        if y0 < y1:
            ystep = 1

        while (not rev and x0 <= x1) or (rev and x1 <= x0):
            # first row
            if steep:
                try:
                    self._fg_bitmap[int(y0), int(x0)] = c
                except IndexError:
                    pass
            else:
                try:
                    self._fg_bitmap[int(x0), int(y0)] = c
                except IndexError:
                    pass
            if y0 != y1 and self._heading % 90 != 0:
                # need a second row to fill the cracks
                j = -1 if y1 < y0 else 1
                if steep:
                    try:
                        self._fg_bitmap[int(y0 + j), int(x0)] = c
                    except IndexError:
                        pass
                else:
                    try:
                        self._fg_bitmap[int(x0), int(y0 + j)] = c
                    except IndexError:
                        pass
            err -= dy
            if err < 0:
                y0 += ystep
                err += dx
            if rev:
                x0 -= 1
            else:
                x0 += 1

    # pylint:enable=too-many-locals, too-many-statements, too-many-branches

    def circle(self, radius, extent=None, steps=None):
        """Draw a circle with given radius. The center is radius units left of
        the turtle; extent - an angle - determines which part of the circle is
        drawn. If extent is not given, draw the entire circle. If extent is not
        a full circle, one endpoint of the arc is the current pen position.
        Draw the arc in counterclockwise direction if radius is positive,
        otherwise in clockwise direction. Finally the direction of the turtle
        is changed by the amount of extent.

        As the circle is approximated by an inscribed regular polygon, steps
        determines the number of steps to use. If not given, it will be
        calculated automatically. May be used to draw regular polygons.

        :param radius: the radius of the circle
        :param extent: the arc of the circle to be drawn
        :param steps: how many points along the arc are computed
        """
        # call: circle(radius)                  # full circle
        # --or: circle(radius, extent)          # arc
        # --or: circle(radius, extent, steps)
        # --or: circle(radius, steps=6)         # 6-sided polygon
        pos = self.pos()
        h = self._heading
        if extent is None:
            extent = self._fullcircle
        if steps is None:
            frac = abs(extent) / self._fullcircle
            steps = int(min(3 + abs(radius) / 4.0, 12.0) * frac) * 4
        w = extent / steps
        w2 = 0.5 * w
        l = radius * math.sin(w * math.pi / 180.0 * self._degreesPerAU)
        if radius < 0:
            l, w, w2 = -l, -w, -w2
        self.left(w2)
        for _ in range(steps - 1):
            self.forward(l)
            self.left(w)
        # rounding error correction on the last step
        self.setheading(self.towards(pos))
        # get back to exact same position and heading
        self.goto(pos)
        self.setheading(h)

    # pylint:disable=inconsistent-return-statements
    def speed(self, speed=None):
        """

        Set the turtle's speed to an integer value in the range 0..10. If no
        argument is given, return current speed.

        If input is a number greater than 10 or smaller than 1, speed is set
        to 0. Speedstrings are mapped to speedvalues as follows:

        "fastest": 0
        "fast": 10
        "normal": 6
        "slow": 3
        "slowest": 1
        Speeds from 1 to 10 enforce increasingly faster animation of line
        drawing and turtle turning.

        Attention: speed = 0 means that no animation takes place.
        forward/back makes turtle jump and likewise left/right make the
        turtle turn instantly.

        :param speed: the new turtle speed (0..10) or None
        """
        if speed is None:
            return self._speed
        if speed > 10 or speed < 1:
            self._speed = 0
        else:
            self._speed = speed

    # pylint:enable=inconsistent-return-statements

    def dot(self, size=None, color=None):
        """Draw a circular dot with diameter size, using color.
        If size is not given, the maximum of pensize+4 and
        2*pensize is used.

        :param size: the diameter of the dot
        :param color: the color of the dot

        """
        if size is None:
            size = max(self._pensize + 4, self._pensize * 2)
        if color is None:
            color = self._pencolor
        else:
            color = self._color_to_pencolor(color)
        pensize = self._pensize
        pencolor = self._pencolor
        down = self.isdown()
        if size > 1:
            self._pensize = size
            self._pencolor = color
            self.pendown()
            self.right(180)
            self.right(180)
            if not down:
                self.penup()
            self._pensize = pensize
            self._pencolor = pencolor
        else:
            self._pensize = 1
            self._plot(self._x, self._y, color)
            self._pensize = pensize

    def stamp(self, bitmap=None, palette=None):
        """
        Stamp a copy of the turtle shape onto the canvas at the current
        turtle position. Return a stamp_id for that stamp, which can be used to
        delete it by calling clearstamp(stamp_id).
        """
        if len(self._fg_addon_group) >= 6:
            print("Addon group full")
            return -1
        s_id = len(self._stamps)
        if self._turtle_pic is None:
            # easy.
            new_stamp = displayio.TileGrid(
                self._turtle_bitmap,
                pixel_shader=self._turtle_palette,
                x=int(self._x - self._turtle_bitmap.width // 2),
                y=int(self._y - self._turtle_bitmap.height // 2),
            )
        elif self._turtle_odb is not None:
            # odb bitmap
            new_stamp = displayio.TileGrid(
                self._turtle_odb,
                pixel_shader=displayio.ColorConverter(),
                x=int(self._x - self._turtle_odb.width // 2),
                y=int(self._y - self._turtle_odb.height // 2),
            )
            self._turtle_odb_use += 1
        else:
            if bitmap is None:
                raise RuntimeError("a bitmap must be provided")
            if palette is None:
                raise RuntimeError("a palette must be provided")
            new_stamp = displayio.TileGrid(
                bitmap,
                pixel_shader=palette,
                x=int(self._x - bitmap.width // 2),
                y=int(self._y - bitmap.height // 2),
            )
        self._fg_addon_group.append(new_stamp)
        if self._turtle_odb is not None:
            self._stamps[s_id] = (new_stamp, self._turtle_odb_file)
        else:
            self._stamps[s_id] = new_stamp

        return s_id

    def clearstamp(self, stampid):
        """

        Delete stamp with given stampid.

        :param stampid: the id of the stamp to be deleted

        """
        if isinstance(stampid, int):
            if stampid in self._stamps and self._stamps[stampid] is not None:
                if isinstance(self._stamps[stampid], tuple):
                    self._fg_addon_group.remove(self._stamps[stampid][0])
                    self._turtle_odb_use -= 1
                    if self._turtle_odb_use == 0:
                        self._stamps[stampid][1].close()
                else:
                    self._fg_addon_group.remove(self._stamps[stampid])
                self._stamps[stampid] = None
            else:
                return
        else:
            raise TypeError("Stamp id must be an int")

    def clearstamps(self, n=None):
        """

        Delete all or first/last n of turtle's stamps. If n is None, delete
        all stamps, if n > 0 delete first n stamps, else if n < 0 delete last
        n stamps.

        :param n: how many stamps to delete (None means delete them all)

        """
        i = 1
        for sid in self._stamps:
            if self._stamps[sid] is not None:
                self.clearstamp(sid)
                if n is not None and i >= n:
                    return
                i += 1

    ###########################################################################
    # Tell turtle's state

    def pos(self):
        """Return the turtle's current location (x,y) (as a Vec2D vector)."""
        return Vec2D(self._x - self._w // 2, self._h // 2 - self._y)

    position = pos

    def towards(self, x1, y1=None):
        """
        Return the angle between the line from turtle position to position
        specified by (x,y) or the vector. This depends on the turtle's start
        orientation which depends on the mode - "standard" or "logo").

        :param x: a number or a pair/vector of numbers
        :param y: a number if x is a number, else None

        """
        if y1 is None:
            y1 = x1[1]
            x1 = x1[0]
        x0, y0 = self.pos()

        result = math.degrees(math.atan2(x1 - x0, y1 - y0))
        result /= self._degreesPerAU
        return (self._angleOffset + self._angleOrient * result) % self._fullcircle

    def xcor(self):
        """Return the turtle's x coordinate."""
        return self._x - self._w // 2

    def ycor(self):
        """Return the turtle's y coordinate."""
        return self._h // 2 - self._y

    def heading(self):
        """Return the turtle's current heading (value depends on the turtle
        mode, see mode()).
        """
        return self._heading

    def distance(self, x1, y1=None):
        """
        Return the distance from the turtle to (x,y) or the vector, in turtle
        step units.

        :param x: a number or a pair/vector of numbers
        :param y: a number if x is a number, else None

        """
        if y1 is None:
            y1 = x1[1]
            x1 = x1[0]
        x0, y0 = self.pos()
        return math.sqrt((x0 - x1) ** 2 + (y0 - y1) ** 2)

    ###########################################################################
    # Setting and measurement

    def _setDegreesPerAU(self, fullcircle):
        """Helper function for degrees() and radians()"""
        self._fullcircle = fullcircle
        self._degreesPerAU = 360 / fullcircle
        if self._logomode:
            self._angleOffset = 0
        else:
            self._angleOffset = -fullcircle / 4

    def degrees(self, fullcircle=360):
        """Set angle measurement units, i.e. set number of "degrees" for
        a full circle.
        Default value is 360 degrees.

        :param fullcircle: the number of degrees in a full circle
        """
        self._setDegreesPerAU(fullcircle)

    def radians(self):
        """Set the angle measurement units to radians.
        Equivalent to degrees(2*math.pi)."""
        self._setDegreesPerAU(2 * math.pi)

    def mode(self, mode=None):
        """

        Set turtle mode ("standard" or "logo") and perform reset.
        If mode is not given, current mode is returned.

        Mode "standard" is compatible with old turtle.
        Mode "logo" is compatible with most Logo turtle graphics.

        :param mode: one of the strings "standard" or "logo"
        """
        if mode == "standard":
            self._logomode = False
            self._angleOrient = -1
            self._angleOffset = self._fullcircle / 4
        elif mode == "logo":
            self._logomode = True
            self._angleOrient = 1
            self._angleOffset = 0
        elif mode is None:
            if self._logomode:
                return "logo"
            return "standard"
        else:
            raise RuntimeError("Mode must be 'logo', 'standard', or None")
        return None

    def window_height(self):
        """
        Return the height of the turtle window."""
        return self._h

    def window_width(self):
        """
        Return the width of the turtle window."""
        return self._w

    ###########################################################################
    # Drawing state

    def pendown(self):
        """Pull the pen down - drawing when moving."""
        self._penstate = True

    pd = pendown
    down = pendown

    def penup(self):
        """Pull the pen up - no drawing when moving."""
        self._penstate = False

    pu = penup
    up = penup

    def isdown(self):
        """Return True if pen is down, False if it's up."""
        return self._penstate

    def pensize(self, width=None):
        """
        Set the line thickness to width or return it.
        If no argument is given, the current pensize is returned.

        :param width: - a positive number

        """
        if width is not None:
            self._pensize = width
        return self._pensize

    width = pensize

    ###########################################################################
    # Color control

    # pylint:disable=no-self-use

    def _color_to_pencolor(self, c):
        return Color.colors.index(c)

    # pylint:enable=no-self-use

    def pencolor(self, c=None):
        """
        Return or set the pencolor.

        pencolor()
            Return the current pencolor as color specification string or as a
            tuple (see example). May be used as input to another color/
            pencolor/fillcolor call.

        pencolor(colorvalue)
            Set pencolor to colorvalue, which is a 24-bit integer such as 0xFF0000.
            The Color class provides the available values:
            BLACK, WHITE, RED, YELLOW, ORANGE, GREEN, BLUE, PURPLE, PINK
            GRAY, LIGHT_GRAY, BROWN, DARK_GREEN, TURQUOISE, DARK_BLUE, DARK_RED

        """
        if c is None:
            return Color.colors[self._pencolor]
        if c not in Color.colors:
            raise RuntimeError("Color must be one of the 'Color' class items")
        self._pencolor = Color.colors.index(c)
        self._turtle_palette[1] = c
        if self._bg_color == self._pencolor:
            self._turtle_palette.make_transparent(1)
        else:
            self._turtle_palette.make_opaque(1)
        return c

    def bgcolor(self, c=None):
        """
        Return or set the background color.

        bgcolor()
            Return the current backgroud color as color specification string.
            May be used as input to another color/ pencolor/fillcolor call.

        bgcolor(colorvalue)
            Set backgroud color to colorvalue, which is a 24-bit integer such as 0xFF0000.
            The Color class provides the available values:
            WHITE, BLACK, RED, ORANGE, YELLOW, GREEN, BLUE, PURPLE, PINK
        """
        if c is None:
            return Color.colors[self._bg_color]
        if c not in Color.colors:
            raise RuntimeError("Color must be one of the 'Color' class items")
        old_color = self._bg_color
        self._fg_palette.make_opaque(old_color)
        self._bg_color = Color.colors.index(c)
        self._bg_palette[0] = c
        self._fg_palette.make_transparent(self._bg_color)
        self._turtle_palette[0] = c
        if self._bg_color == self._pencolor:
            self._turtle_palette.make_transparent(1)
        else:
            self._turtle_palette.make_opaque(1)
        for h in range(self._h):
            for w in range(self._w):
                if self._fg_bitmap[w, h] == old_color:
                    self._fg_bitmap[w, h] = self._bg_color
        return Color.colors[self._bg_color]

    # pylint:disable=inconsistent-return-statements
    def bgpic(self, picname=None):
        """Set background image or return name of current backgroundimage.
        Optional argument:
        picname -- a string, name of an image file or "nopic".
        If picname is a filename, set the corresponding image as background.
        If picname is "nopic", delete backgroundimage, if present.
        If picname is None, return the filename of the current backgroundimage.
        """
        if picname is None:
            return self._bg_pic_filename
        if picname == "nopic":
            if self._bg_pic is not None:
                self._bg_addon_group.remove(self._odb_tilegrid)
                self._odb_tilegrid = None
                self._bg_pic.close()
                self._bg_pic = None
                self._bg_pic_filename = ""
        else:
            self._bg_pic = open(picname, "rb")
            odb = displayio.OnDiskBitmap(self._bg_pic)
            self._odb_tilegrid = displayio.TileGrid(
                odb, pixel_shader=displayio.ColorConverter()
            )
            self._bg_addon_group.append(self._odb_tilegrid)
            self._bg_pic_filename = picname
            # centered
            self._odb_tilegrid.y = ((self._h * self._fg_scale) // 2) - (odb.height // 2)
            self._odb_tilegrid.x = ((self._w * self._fg_scale) // 2) - (odb.width // 2)

    # pylint:enable=inconsistent-return-statements

    ###########################################################################
    # More drawing control

    def reset(self):
        """
        Delete the turtle's drawings from the screen, re-center the turtle
        and set variables to the default values."""
        self.changeturtle()
        self.bgpic("nopic")
        self.bgcolor(Color.BLACK)
        self.clear()
        self.penup()
        self.goto(0, 0)
        self.setheading(0)
        self.pensize(1)
        self.pencolor(Color.WHITE)

    def clear(self):
        """Delete the turtle's drawings from the screen. Do not move turtle."""
        self.clearstamps()
        for w in range(self._w):
            for h in range(self._h):
                self._fg_bitmap[w, h] = self._bg_color
        for i, c in enumerate(Color.colors):
            self._fg_palette[i] = c ^ 0xFFFFFF
        for i, c in enumerate(Color.colors):
            self._fg_palette[i] = c
        time.sleep(0.1)

    ###########################################################################
    # Visibility

    def showturtle(self):
        """
        Make the turtle visible."""
        if self._turtle_group:
            return
        if self._turtle_pic is None:
            self._turtle_group.append(self._turtle_sprite)
        else:
            self._turtle_group.append(self._turtle_alt_sprite)

    st = showturtle

    def hideturtle(self):
        """
        Make the turtle invisible."""
        if not self._turtle_group:
            return
        self._turtle_group.pop()

    ht = hideturtle

    def isvisible(self):
        """
        Return True if the Turtle is shown, False if it's hidden."""
        if self._turtle_group:
            return True
        return False

    # pylint:disable=too-many-statements, too-many-branches
    def changeturtle(self, source=None, dimensions=(12, 12)):
        """
        Change the turtle.
        if a string is provided, its a path to an image opened via OnDiskBitmap
        if a tilegrid is provided, it replace the default one for the turtle shape.
        if no argument is provided, the default shape will be restored
        """
        if source is None:
            if self._turtle_pic is None:
                return
            if self._turtle_group:
                self._turtle_group.remove(self._turtle_alt_sprite)
                self._turtle_group.append(self._turtle_sprite)
            self._turtle_alt_sprite = None
            if self._turtle_odb is not None:
                self._turtle_odb_use -= 1
                self._turtle_odb = None
            if self._turtle_odb_file is not None:
                if self._turtle_odb_use == 0:
                    self._turtle_odb_file.close()
                self._turtle_odb_file = None
            self._turtle_pic = None
            self._drawturtle()
            return
        if isinstance(source, str):
            visible = self.isvisible()
            if self._turtle_pic is not None:
                if self._turtle_group:
                    self._turtle_group.remove(self._turtle_alt_sprite)
                self._turtle_alt_sprite = None
                self._turtle_odb = None
                if not isinstance(self._turtle_pic, tuple):
                    self._turtle_odb_file.close()
                    self._turtle_odb_file = None
                    self._turtle_odb_use -= 1
                self._turtle_pic = None
            self._turtle_odb_file = open(source, "rb")
            try:
                self._turtle_odb = displayio.OnDiskBitmap(self._turtle_odb_file)
            except:
                self._turtle_odb_file.close()
                self._turtle_odb_file = None
                self._turtle_pic = None
                if visible:
                    self._turtle_group.append(self._turtle_sprite)
                raise
            self._turtle_odb_use += 1
            self._turtle_pic = True
            self._turtle_alt_sprite = displayio.TileGrid(
                self._turtle_odb, pixel_shader=displayio.ColorConverter()
            )

            if self._turtle_group:
                self._turtle_group.pop()
            if visible:
                self._turtle_group.append(self._turtle_alt_sprite)
            self._drawturtle()
        elif isinstance(source, displayio.TileGrid):
            if self._turtle_pic is not None:
                if self._turtle_odb_file is not None:
                    self._turtle_odb_use -= 1
                    if self._turtle_odb_use == 0:
                        self._turtle_odb_file.close()
            self._turtle_pic = dimensions
            self._turtle_alt_sprite = source
            if self._turtle_group:
                self._turtle_group.pop()
                self._turtle_group.append(self._turtle_alt_sprite)
            self._drawturtle()
        else:
            raise TypeError(
                'Argument must be "str", a "displayio.TileGrid" or nothing.'
            )

    # pylint:enable=too-many-statements, too-many-branches

    ###########################################################################
    # Other

    def _turn(self, angle):
        if angle % self._fullcircle == 0:
            return
        if not self.isdown() or self._pensize == 1:
            self._heading += angle
            self._heading %= self._fullcircle  # wrap
            return
        start_angle = self._heading
        steps = math.ceil(
            (self._pensize * 2) * 3.1415 * (abs(angle) / self._fullcircle)
        )
        if steps < 1:
            d_angle = angle
            steps = 1
        else:
            d_angle = angle / steps

        if d_angle > 0:
            d_angle = math.ceil(d_angle)
        elif d_angle < 0:
            d_angle = math.floor(d_angle)
        else:
            print("d_angle = 0 !", d_angle, angle, steps)
            if self._logomode:
                self._heading += angle
            else:
                self._heading -= angle
            self._heading %= self._fullcircle  # wrap
            return

        if abs(angle - steps * d_angle) >= abs(d_angle):
            steps += abs(angle - steps * d_angle) // abs(d_angle)

        self._plot(self._x, self._y, self._pencolor)
        for _ in range(steps):
            self._heading += d_angle
            self._heading %= self._fullcircle  # wrap
            self._plot(self._x, self._y, self._pencolor)

        # error correction
        if self._heading != (start_angle + angle) % self._fullcircle:
            self._heading = start_angle + angle
            self._heading %= self._fullcircle
            self._plot(self._x, self._y, self._pencolor)

    def _GCD(self, a, b):
        """GCD(a,b):
        recursive 'Greatest common divisor' calculus for int numbers a and b"""
        if b == 0:
            return a
        r = a % b
        return self._GCD(b, r)
