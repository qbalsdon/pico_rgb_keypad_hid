# SPDX-FileCopyrightText: 2019 Scott Shawcroft for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_display_text.label`
====================================================

Displays text labels using CircuitPython's displayio.

* Author(s): Scott Shawcroft

Implementation Notes
--------------------

**Hardware:**

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://github.com/adafruit/circuitpython/releases

"""

import displayio

__version__ = "2.12.4"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_Display_Text.git"


class Label(displayio.Group):
    """A label displaying a string of text. The origin point set by ``x`` and ``y``
    properties will be the left edge of the bounding box, and in the center of a M
    glyph (if its one line), or the (number of lines * linespacing + M)/2. That is,
    it will try to have it be center-left as close as possible.

    :param Font font: A font class that has ``get_bounding_box`` and ``get_glyph``.
      Must include a capital M for measuring character size.
    :param str text: Text to display
    :param int max_glyphs: The largest quantity of glyphs we will display
    :param int color: Color of all text in RGB hex
    :param float line_spacing: Line spacing of text to display
    :param bool background_tight: Set `True` only if you want background box to tightly
     surround text. When set to 'True' Padding parameters will be ignored.
    :param int padding_top: Additional pixels added to background bounding box at top.
     This parameter could be negative indicating additional pixels subtracted to background
     bounding box.
    :param int padding_bottom: Additional pixels added to background bounding box at bottom.
     This parameter could be negative indicating additional pixels subtracted to background
     bounding box.
    :param int padding_left: Additional pixels added to background bounding box at left.
     This parameter could be negative indicating additional pixels subtracted to background
     bounding box.
    :param int padding_right: Additional pixels added to background bounding box at right.
     This parameter could be negative indicating additional pixels subtracted to background
     bounding box.
    :param (float,float) anchor_point: Point that anchored_position moves relative to.
     Tuple with decimal percentage of width and height.
     (E.g. (0,0) is top left, (1.0, 0.5): is middle right.)
    :param (int,int) anchored_position: Position relative to the anchor_point. Tuple
     containing x,y pixel coordinates.
    :param int scale: Integer value of the pixel scaling"""

    # pylint: disable=too-many-instance-attributes, too-many-locals
    # This has a lot of getters/setters, maybe it needs cleanup.

    def __init__(
        self,
        font,
        *,
        x=0,
        y=0,
        text="",
        max_glyphs=None,
        color=0xFFFFFF,
        background_color=None,
        line_spacing=1.25,
        background_tight=False,
        padding_top=0,
        padding_bottom=0,
        padding_left=0,
        padding_right=0,
        anchor_point=None,
        anchored_position=None,
        scale=1,
        **kwargs
    ):
        if not max_glyphs and not text:
            raise RuntimeError("Please provide a max size, or initial text")
        if not max_glyphs:
            max_glyphs = len(text)
        # add one to max_size for the background bitmap tileGrid

        # instance the Group
        # self Group will contain a single local_group which contains a Group (self.local_group)
        # which contains a TileGrid
        # The self scale should always be 1
        super().__init__(max_size=1, scale=1, **kwargs)
        # local_group will set the scale
        self.local_group = displayio.Group(max_size=max_glyphs + 1, scale=scale)
        self.append(self.local_group)

        self.width = max_glyphs
        self._font = font
        self._text = None
        self._anchor_point = anchor_point
        self.x = x
        self.y = y

        self.height = self._font.get_bounding_box()[1]
        self._line_spacing = line_spacing
        self._boundingbox = None

        self._background_tight = (
            background_tight  # sets padding status for text background box
        )

        # Create the two-color text palette
        self.palette = displayio.Palette(2)
        self.palette[0] = 0
        self.palette.make_transparent(0)
        self.color = color

        self._background_color = background_color
        self._background_palette = displayio.Palette(1)
        self._added_background_tilegrid = False

        self._padding_top = padding_top
        self._padding_bottom = padding_bottom
        self._padding_left = padding_left
        self._padding_right = padding_right

        if text is not None:
            self._update_text(str(text))
        if (anchored_position is not None) and (anchor_point is not None):
            self.anchored_position = anchored_position

    def _create_background_box(self, lines, y_offset):
        """Private Class function to create a background_box
        :param lines: int number of lines
        :param y_offset: int y pixel bottom coordinate for the background_box"""

        left = self._boundingbox[0]

        if self._background_tight:  # draw a tight bounding box
            box_width = self._boundingbox[2]
            box_height = self._boundingbox[3]
            x_box_offset = 0
            y_box_offset = self._boundingbox[1]

        else:  # draw a "loose" bounding box to include any ascenders/descenders.
            ascent, descent = self._get_ascent_descent()

            box_width = self._boundingbox[2] + self._padding_left + self._padding_right
            x_box_offset = -self._padding_left
            box_height = (
                (ascent + descent)
                + int((lines - 1) * self.height * self._line_spacing)
                + self._padding_top
                + self._padding_bottom
            )
            y_box_offset = -ascent + y_offset - self._padding_top

        box_width = max(0, box_width)  # remove any negative values
        box_height = max(0, box_height)  # remove any negative values

        background_bitmap = displayio.Bitmap(box_width, box_height, 1)
        tile_grid = displayio.TileGrid(
            background_bitmap,
            pixel_shader=self._background_palette,
            x=left + x_box_offset,
            y=y_box_offset,
        )

        return tile_grid

    def _get_ascent_descent(self):
        """ Private function to calculate ascent and descent font values """
        if hasattr(self.font, "ascent"):
            return self.font.ascent, self.font.descent

        # check a few glyphs for maximum ascender and descender height
        glyphs = "M j'"  # choose glyphs with highest ascender and lowest
        try:
            self._font.load_glyphs(glyphs)
        except AttributeError:
            # Builtin font doesn't have or need load_glyphs
            pass
        # descender, will depend upon font used
        ascender_max = descender_max = 0
        for char in glyphs:
            this_glyph = self._font.get_glyph(ord(char))
            if this_glyph:
                ascender_max = max(ascender_max, this_glyph.height + this_glyph.dy)
                descender_max = max(descender_max, -this_glyph.dy)
        return ascender_max, descender_max

    def _get_ascent(self):
        return self._get_ascent_descent()[0]

    def _update_background_color(self, new_color):
        """Private class function that allows updating the font box background color
        :param new_color: int color as an RGB hex number."""

        if new_color is None:
            self._background_palette.make_transparent(0)
            if self._added_background_tilegrid:
                self.local_group.pop(0)
                self._added_background_tilegrid = False
        else:
            self._background_palette.make_opaque(0)
            self._background_palette[0] = new_color
        self._background_color = new_color

        lines = self._text.rstrip("\n").count("\n") + 1
        y_offset = self._get_ascent() // 2

        if not self._added_background_tilegrid:  # no bitmap is in the self Group
            # add bitmap if text is present and bitmap sizes > 0 pixels
            if (
                (len(self._text) > 0)
                and (
                    self._boundingbox[2] + self._padding_left + self._padding_right > 0
                )
                and (
                    self._boundingbox[3] + self._padding_top + self._padding_bottom > 0
                )
            ):
                # This can be simplified in CP v6.0, when group.append(0) bug is corrected
                if len(self.local_group) > 0:
                    self.local_group.insert(
                        0, self._create_background_box(lines, y_offset)
                    )
                else:
                    self.local_group.append(
                        self._create_background_box(lines, y_offset)
                    )
                self._added_background_tilegrid = True

        else:  # a bitmap is present in the self Group
            # update bitmap if text is present and bitmap sizes > 0 pixels
            if (
                (len(self._text) > 0)
                and (
                    self._boundingbox[2] + self._padding_left + self._padding_right > 0
                )
                and (
                    self._boundingbox[3] + self._padding_top + self._padding_bottom > 0
                )
            ):
                self.local_group[0] = self._create_background_box(lines, y_offset)
            else:  # delete the existing bitmap
                self.local_group.pop(0)
                self._added_background_tilegrid = False

    def _update_text(
        self, new_text
    ):  # pylint: disable=too-many-locals ,too-many-branches, too-many-statements
        x = 0
        y = 0
        if self._added_background_tilegrid:
            i = 1
        else:
            i = 0
        tilegrid_count = i

        y_offset = self._get_ascent() // 2

        right = top = bottom = 0
        left = None

        for character in new_text:
            if character == "\n":
                y += int(self.height * self._line_spacing)
                x = 0
                continue
            glyph = self._font.get_glyph(ord(character))
            if not glyph:
                continue
            right = max(right, x + glyph.shift_x, x + glyph.width + glyph.dx)
            if x == 0:
                if left is None:
                    left = glyph.dx
                else:
                    left = min(left, glyph.dx)
            if y == 0:  # first line, find the Ascender height
                top = min(top, -glyph.height - glyph.dy + y_offset)
            bottom = max(bottom, y - glyph.dy + y_offset)
            position_y = y - glyph.height - glyph.dy + y_offset
            position_x = x + glyph.dx
            if glyph.width > 0 and glyph.height > 0:
                try:
                    # pylint: disable=unexpected-keyword-arg
                    face = displayio.TileGrid(
                        glyph.bitmap,
                        pixel_shader=self.palette,
                        default_tile=glyph.tile_index,
                        tile_width=glyph.width,
                        tile_height=glyph.height,
                        position=(position_x, position_y),
                    )
                except TypeError:
                    face = displayio.TileGrid(
                        glyph.bitmap,
                        pixel_shader=self.palette,
                        default_tile=glyph.tile_index,
                        tile_width=glyph.width,
                        tile_height=glyph.height,
                        x=position_x,
                        y=position_y,
                    )
                if tilegrid_count < len(self.local_group):
                    self.local_group[tilegrid_count] = face
                else:
                    self.local_group.append(face)
                tilegrid_count += 1
            x += glyph.shift_x
            i += 1
        # Remove the rest

        if left is None:
            left = 0

        while len(self.local_group) > tilegrid_count:  # i:
            self.local_group.pop()
        self._text = new_text
        self._boundingbox = (left, top, right - left, bottom - top)

        if self.background_color is not None:
            self._update_background_color(self._background_color)

    @property
    def bounding_box(self):
        """An (x, y, w, h) tuple that completely covers all glyphs. The
        first two numbers are offset from the x, y origin of this group"""
        return tuple(self._boundingbox)

    @property
    def line_spacing(self):
        """The amount of space between lines of text, in multiples of the font's
        bounding-box height. (E.g. 1.0 is the bounding-box height)"""
        return self._line_spacing

    @line_spacing.setter
    def line_spacing(self, spacing):
        self._line_spacing = spacing
        self.text = self._text  # redraw the box

    @property
    def color(self):
        """Color of the text as an RGB hex number."""
        return self.palette[1]

    @color.setter
    def color(self, new_color):
        self._color = new_color
        if new_color is not None:
            self.palette[1] = new_color
            self.palette.make_opaque(1)
        else:
            self.palette[1] = 0
            self.palette.make_transparent(1)

    @property
    def background_color(self):
        """Color of the background as an RGB hex number."""
        return self._background_color

    @background_color.setter
    def background_color(self, new_color):
        self._update_background_color(new_color)

    @property
    def text(self):
        """Text to display."""
        return self._text

    @text.setter
    def text(self, new_text):
        try:
            current_anchored_position = self.anchored_position
            self._update_text(str(new_text))
            self.anchored_position = current_anchored_position
        except RuntimeError as run_error:
            raise RuntimeError("Text length exceeds max_glyphs") from run_error

    @property
    def scale(self):
        """Set the scaling of the label, in integer values"""
        return self.local_group.scale

    @scale.setter
    def scale(self, new_scale):
        current_anchored_position = self.anchored_position
        self.local_group.scale = new_scale
        self.anchored_position = current_anchored_position

    @property
    def font(self):
        """Font to use for text display."""
        return self._font

    @font.setter
    def font(self, new_font):
        old_text = self._text
        current_anchored_position = self.anchored_position
        self._text = ""
        self._font = new_font
        self.height = self._font.get_bounding_box()[1]
        self._update_text(str(old_text))
        self.anchored_position = current_anchored_position

    @property
    def anchor_point(self):
        """Point that anchored_position moves relative to.
        Tuple with decimal percentage of width and height.
        (E.g. (0,0) is top left, (1.0, 0.5): is middle right.)"""
        return self._anchor_point

    @anchor_point.setter
    def anchor_point(self, new_anchor_point):
        if self._anchor_point is not None:
            current_anchored_position = self.anchored_position
            self._anchor_point = new_anchor_point
            self.anchored_position = current_anchored_position
        else:
            self._anchor_point = new_anchor_point

    @property
    def anchored_position(self):
        """Position relative to the anchor_point. Tuple containing x,y
        pixel coordinates."""
        if self._anchor_point is None:
            return None
        return (
            int(
                self.x
                + (self._boundingbox[0] * self.scale)
                + round(self._anchor_point[0] * self._boundingbox[2] * self.scale)
            ),
            int(
                self.y
                + (self._boundingbox[1] * self.scale)
                + round(self._anchor_point[1] * self._boundingbox[3] * self.scale)
            ),
        )

    @anchored_position.setter
    def anchored_position(self, new_position):
        if (self._anchor_point is None) or (new_position is None):
            return  # Note: anchor_point must be set before setting anchored_position
        self.x = int(
            new_position[0]
            - (self._boundingbox[0] * self.scale)
            - round(self._anchor_point[0] * (self._boundingbox[2] * self.scale))
        )
        self.y = int(
            new_position[1]
            - (self._boundingbox[1] * self.scale)
            - round(self._anchor_point[1] * self._boundingbox[3] * self.scale)
        )
