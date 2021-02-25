# SPDX-FileCopyrightText: 2018 Kattni Rembor for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_slideshow`
====================================================
CircuitPython helper library for displaying a slideshow of images on a display.

* Author(s): Kattni Rembor, Carter Nelson, Roy Hooper, Melissa LeBlanc-Williams

Implementation Notes
--------------------

**Hardware:**

 * `Adafruit Hallowing M0 Express <https://www.adafruit.com/product/3900>`_

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://github.com/adafruit/circuitpython/releases

"""
import time
import os
import random
import displayio

try:
    # text slides are an optional feature and require adafruit_display_text
    from adafruit_display_text import bitmap_label
    import terminalio
    import json

    TEXT_SLIDES_ENABLED = True
except ImportError:
    print("Warning: adafruit_display_text not found. No support for text slides.")
    TEXT_SLIDES_ENABLED = False

try:
    # custom fonts are an optional feature and require adafruit_bitmap_font
    from adafruit_bitmap_font import bitmap_font

    CUSTOM_FONTS = True
except ImportError:
    print("Warning: adafruit_bitmap_font not found. No support for custom fonts.")
    CUSTOM_FONTS = False

__version__ = "1.5.6"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_Slideshow.git"


class HorizontalAlignment:
    """Defines possible horizontal alignment orders."""

    # pylint: disable=too-few-public-methods
    LEFT = 1
    CENTER = 2
    RIGHT = 3
    # pylint: enable=too-few-public-methods


class VerticalAlignment:
    """Defines possible vertical alignment orders."""

    # pylint: disable=too-few-public-methods
    TOP = 1
    CENTER = 2
    BOTTOM = 3
    # pylint: enable=too-few-public-methods


class PlayBackOrder:
    """Defines possible slideshow playback orders."""

    # pylint: disable=too-few-public-methods
    ALPHABETICAL = 0
    """Orders by alphabetical sort of filenames"""

    RANDOM = 1
    """Randomly shuffles the images"""
    # pylint: enable=too-few-public-methods


class PlayBackDirection:
    """Defines possible slideshow playback directions."""

    # pylint: disable=too-few-public-methods
    BACKWARD = -1
    """The next image is before the current image. When alphabetically sorted, this is towards A."""

    FORWARD = 1
    """The next image is after the current image. When alphabetically sorted, this is towards Z."""
    # pylint: enable=too-few-public-methods


class SlideShow:
    # pylint: disable=too-many-instance-attributes
    """
    Class for displaying a slideshow of .bmp images on displays.

    :param str folder: Specify the folder containing the image files, in quotes. Default is
                       the root directory, ``"/"``.

    :param PlayBackOrder order: The order in which the images display. You can choose random
                                (``RANDOM``) or alphabetical (``ALPHABETICAL``). Default is
                                ``ALPHABETICAL``.

    :param bool loop: Specify whether to loop the images or play through the list once. `True`
                 if slideshow will continue to loop, ``False`` if it will play only once.
                 Default is ``True``.

    :param int dwell: The number of seconds each image displays, in seconds. Default is 3.

    :param bool fade_effect: Specify whether to include the fade effect between images. ``True``
                        tells the code to fade the backlight up and down between image display
                        transitions. ``False`` maintains max brightness on the backlight between
                        image transitions. Default is ``True``.

    :param bool auto_advance: Specify whether to automatically advance after dwell seconds. ``True``
                 if slideshow should auto play, ``False`` if you want to control advancement
                 manually.  Default is ``True``.

    :param PlayBackDirection direction: The playback direction.

    :param HorizonalAlignment h_align: The Horizontal alignment of smaller/larger images

    :param VerticalAlignment v_align: The Vertical alignment of smaller/larger images

    Example code for Hallowing Express. With this example, the slideshow will play through once
    in alphabetical order:

    .. code-block:: python

        from adafruit_slideshow import PlayBackOrder, SlideShow
        import board
        import pulseio

        slideshow = SlideShow(board.DISPLAY, pulseio.PWMOut(board.TFT_BACKLIGHT), folder="/",
                              loop=False, order=PlayBackOrder.ALPHABETICAL)

        while slideshow.update():
            pass

    Example code for Hallowing Express. Sets ``dwell`` to 0 seconds, turns ``auto_advance`` off,
    and uses capacitive touch to advance backwards and forwards through the images and to control
    the brightness level of the backlight:

    .. code-block:: python

        from adafruit_slideshow import PlayBackOrder, SlideShow, PlayBackDirection
        import touchio
        import board
        import pulseio

        forward_button = touchio.TouchIn(board.TOUCH4)
        back_button = touchio.TouchIn(board.TOUCH1)

        brightness_up = touchio.TouchIn(board.TOUCH3)
        brightness_down = touchio.TouchIn(board.TOUCH2)

        slideshow = SlideShow(board.DISPLAY, pulseio.PWMOut(board.TFT_BACKLIGHT), folder="/",
                              auto_advance=False, dwell=0)

        while True:
            if forward_button.value:
                slideshow.direction = PlayBackDirection.FORWARD
                slideshow.advance()
            if back_button.value:
                slideshow.direction = PlayBackDirection.BACKWARD
                slideshow.advance()

            if brightness_up.value:
                slideshow.brightness += 0.001
            elif brightness_down.value:
                slideshow.brightness -= 0.001
    """

    def __init__(
        self,
        display,
        backlight_pwm=None,
        *,
        folder="/",
        order=PlayBackOrder.ALPHABETICAL,
        loop=True,
        dwell=3,
        fade_effect=True,
        auto_advance=True,
        direction=PlayBackDirection.FORWARD,
        h_align=HorizontalAlignment.LEFT,
        v_align=VerticalAlignment.TOP,
    ):
        def _check_json_file(file):
            if TEXT_SLIDES_ENABLED:
                if file.endswith(".json"):
                    with open(file) as _file_obj:
                        try:
                            json_data = json.loads(_file_obj.read())
                            if "text" in json_data:
                                return True
                        except ValueError:
                            return False
            return False

        self.loop = loop
        """Specifies whether to loop through the slides continuously or play through the list once.
        ``True`` will continue to loop, ``False`` will play only once."""

        self.dwell = dwell
        """The number of seconds each slide displays, in seconds."""

        self.direction = direction
        """Specify the playback direction.  Default is ``PlayBackDirection.FORWARD``.  Can also be
        ``PlayBackDirection.BACKWARD``."""

        self.auto_advance = auto_advance
        """Enable auto-advance based on dwell time.  Set to ``False`` to manually control."""

        self.fade_effect = fade_effect
        """Whether to include the fade effect between slides. ``True`` tells the code to fade the
           backlight up and down between slide display transitions. ``False`` maintains max
           brightness on the backlight between slide transitions."""

        # Load the image names before setting order so they can be reordered.
        self._img_start = None
        self._file_list = [
            folder + "/" + f
            for f in os.listdir(folder)
            if (
                not f.startswith(".")
                and (f.endswith(".bmp") or _check_json_file(folder + "/" + f))
            )
        ]

        self._order = None
        self.order = order
        """The order in which the images display. You can choose random (``RANDOM``) or
           alphabetical (``ALPHA``)."""

        # Default positioning
        self._h_align = h_align
        self._v_align = v_align

        self._current_slide_index = -1
        self._slide_file = None
        self._brightness = 0.5

        # Setup the display
        self._group = displayio.Group()
        self._display = display
        display.show(self._group)

        self._backlight_pwm = backlight_pwm
        if (
            not backlight_pwm
            and fade_effect
            and hasattr(self._display, "auto_brightness")
        ):
            self._display.auto_brightness = False

        # Show the first image
        self.advance()

    @property
    def current_slide_name(self):
        """Returns the current image name."""
        return self._file_list[self._current_slide_index]

    @property
    def order(self):
        """Specifies the order in which the images are displayed. Options are random (``RANDOM``) or
        alphabetical (``ALPHABETICAL``). Default is ``RANDOM``."""
        return self._order

    @order.setter
    def order(self, order):
        if order not in [PlayBackOrder.ALPHABETICAL, PlayBackOrder.RANDOM]:
            raise ValueError("Order must be either 'RANDOM' or 'ALPHABETICAL'")

        self._order = order
        self._reorder_slides()

    def _reorder_slides(self):
        if self.order == PlayBackOrder.ALPHABETICAL:
            self._file_list = sorted(self._file_list)
        elif self.order == PlayBackOrder.RANDOM:
            self._file_list = sorted(self._file_list, key=lambda x: random.random())

    def _set_backlight(self, brightness):
        if self._backlight_pwm:
            full_brightness = 2 ** 16 - 1
            self._backlight_pwm.duty_cycle = int(full_brightness * brightness)
        else:
            try:
                self._display.brightness = brightness
            except (RuntimeError, AttributeError):
                pass

    @property
    def brightness(self):
        """Brightness of the backlight when an image is displaying. Clamps to 0 to 1.0"""
        return self._brightness

    @brightness.setter
    def brightness(self, brightness):
        if brightness < 0:
            brightness = 0
        elif brightness > 1.0:
            brightness = 1.0
        self._brightness = brightness
        self._set_backlight(brightness)

    def _fade_up(self):
        if not self.fade_effect:
            self._set_backlight(self.brightness)
            return
        steps = 100
        for i in range(steps):
            self._set_backlight(self.brightness * i / steps)
            time.sleep(0.01)

    def _fade_down(self):
        if not self.fade_effect:
            self._set_backlight(self.brightness)
            return
        steps = 100
        for i in range(steps, -1, -1):
            self._set_backlight(self.brightness * i / steps)
            time.sleep(0.01)

    def _create_label(self, file):
        # pylint: disable=too-many-branches
        """Creates and returns a label from a file object that contains
        valid valid json describing the text to use.
        See: examples/sample_text_slide.json
        """
        json_data = json.loads(file.read())
        _scale = 1
        if "scale" in json_data:
            _scale = int(json_data["scale"])

        if CUSTOM_FONTS:
            if "font" in json_data:
                _font = bitmap_font.load_font(json_data["font"])
            else:
                _font = terminalio.FONT
        else:
            _font = terminalio.FONT

        label = bitmap_label.Label(_font, text=json_data["text"], scale=_scale)
        if "h_align" not in json_data or json_data["h_align"] == "LEFT":
            x_anchor_point = 0.0
            x_anchored_position = 0
        elif json_data["h_align"] == "CENTER":
            x_anchor_point = 0.5
            x_anchored_position = self._display.width // 2
        elif json_data["h_align"] == "RIGHT":
            x_anchor_point = 1.0
            x_anchored_position = self._display.width - 1
        else:
            # wrong value for align
            x_anchor_point = 0.0
            x_anchored_position = 0

        if "v_align" not in json_data or json_data["v_align"] == "TOP":
            y_anchor_point = 0.0
            y_anchored_position = 0
        elif json_data["v_align"] == "CENTER":
            y_anchor_point = 0.5
            y_anchored_position = self._display.height // 2
        elif json_data["v_align"] == "BOTTOM":
            y_anchor_point = 1.0
            y_anchored_position = self._display.height - 1
        else:
            # wrong value for align
            y_anchor_point = 0.0
            y_anchored_position = 0

        if "background_color" in json_data:
            label.background_color = int(json_data["background_color"], 16)

        if "color" in json_data:
            label.color = int(json_data["color"], 16)

        label.anchor_point = (x_anchor_point, y_anchor_point)
        label.anchored_position = (x_anchored_position, y_anchored_position)
        return label

    def update(self):
        """Updates the slideshow to the next image."""
        now = time.monotonic()
        if not self.auto_advance or now - self._img_start < self.dwell:
            return True
        return self.advance()

    # pylint: disable=too-many-branches, too-many-statements
    def advance(self):
        """Displays the next image. Returns True when a new image was displayed, False otherwise."""
        if self._slide_file:
            self._fade_down()
            self._group.pop()
            self._slide_file.close()
            self._slide_file = None

        self._current_slide_index += self.direction

        # Try to load slides until a valid file is found or we run out of options. This
        # loop stops because we either set odb or reduce the length of _file_list.
        odb = None
        lbl = None
        while not odb and not lbl and self._file_list:
            if 0 <= self._current_slide_index < len(self._file_list):
                pass
            elif not self.loop:
                return False
            else:
                slide_count = len(self._file_list)
                if self._current_slide_index < 0:
                    self._current_slide_index += slide_count
                elif self._current_slide_index >= slide_count:
                    self._current_slide_index -= slide_count
                self._reorder_slides()

            file_name = self._file_list[self._current_slide_index]
            self._slide_file = open(file_name, "rb")
            if file_name.endswith(".bmp"):
                try:
                    odb = displayio.OnDiskBitmap(self._slide_file)
                except ValueError:
                    self._slide_file.close()
                    self._slide_file = None
                    del self._file_list[self._current_slide_index]
            elif file_name.endswith(".json"):
                lbl = self._create_label(self._slide_file)

        if not odb and not lbl:
            raise RuntimeError("No valid images or text json files")

        if odb:
            if self._h_align == HorizontalAlignment.RIGHT:
                self._group.x = self._display.width - odb.width
            elif self._h_align == HorizontalAlignment.CENTER:
                self._group.x = round(self._display.width / 2 - odb.width / 2)
            else:
                self._group.x = 0

            if self._v_align == VerticalAlignment.BOTTOM:
                self._group.y = self._display.height - odb.height
            elif self._v_align == VerticalAlignment.CENTER:
                self._group.y = round(self._display.height / 2 - odb.height / 2)
            else:
                self._group.y = 0

            image_tilegrid = displayio.TileGrid(
                odb, pixel_shader=displayio.ColorConverter()
            )

            self._group.append(image_tilegrid)
        if lbl:
            self._group.append(lbl)

        if hasattr(self._display, "refresh"):
            self._display.refresh()
        self._fade_up()
        self._img_start = time.monotonic()

        return True

    # pylint: enable=too-many-branches

    @property
    def h_align(self):
        """Get or Set the Horizontal Alignment"""
        return self._h_align

    @h_align.setter
    def h_align(self, val):
        if val not in (
            HorizontalAlignment.LEFT,
            HorizontalAlignment.CENTER,
            HorizontalAlignment.RIGHT,
        ):
            raise ValueError("Alignment must be LEFT, RIGHT, or CENTER")
        self._h_align = val

    @property
    def v_align(self):
        """Get or Set the Vertical Alignment"""
        return self._v_align

    @v_align.setter
    def v_align(self, val):
        if val not in (
            VerticalAlignment.TOP,
            VerticalAlignment.CENTER,
            VerticalAlignment.BOTTOM,
        ):
            raise ValueError("Alignment must be TOP, BOTTOM, or CENTER")
        self._v_align = val
