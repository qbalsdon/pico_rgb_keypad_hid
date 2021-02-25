# SPDX-FileCopyrightText: 2020 Melissa LeBlanc-Williams, written for Adafruit Industries
#
# SPDX-License-Identifier: Unlicense
"""
`adafruit_matrixportal.matrixportal`
================================================================================

Helper library for the MatrixPortal M4 or Adafruit RGB Matrix Shield + Metro M4 Airlift Lite.

* Author(s): Melissa LeBlanc-Williams

Implementation Notes
--------------------

**Hardware:**

* `Adafruit MatrixPortal M4 <https://www.adafruit.com/product/4745>`_
* `Adafruit Metro M4 Express AirLift <https://www.adafruit.com/product/4000>`_
* `Adafruit RGB Matrix Shield <https://www.adafruit.com/product/2601>`_
* `64x32 RGB LED Matrix <https://www.adafruit.com/product/2278>`_

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://github.com/adafruit/circuitpython/releases

"""

import gc
from time import sleep
import terminalio
from adafruit_portalbase import PortalBase
from adafruit_matrixportal.network import Network
from adafruit_matrixportal.graphics import Graphics

__version__ = "2.1.0"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_MatrixPortal.git"


class MatrixPortal(PortalBase):
    """Class representing the Adafruit RGB Matrix Portal.

    :param url: The URL of your data source. Defaults to ``None``.
    :param headers: The headers for authentication, typically used by Azure API's.
    :param json_path: The list of json traversal to get data out of. Can be list of lists for
                      multiple data points. Defaults to ``None`` to not use json.
    :param regexp_path: The list of regexp strings to get data out (use a single regexp group). Can
                        be list of regexps for multiple data points. Defaults to ``None`` to not
                        use regexp.
    :param default_bg: The path to your default background image file or a hex color.
                       Defaults to 0x000000.
    :param status_neopixel: The pin for the status NeoPixel. Use ``board.NEOPIXEL`` for the on-board
                            NeoPixel. Defaults to ``None``, not the status LED
    :param json_transform: A function or a list of functions to call with the parsed JSON.
                           Changes and additions are permitted for the ``dict`` object.
    :param esp: A passed ESP32 object, Can be used in cases where the ESP32 chip needs to be used
                             before calling the pyportal class. Defaults to ``None``.
    :param busio.SPI external_spi: A previously declared spi object. Defaults to ``None``.
    :param int bit_depth: The number of bits per color channel. Defaults to 2.
    :param list alt_addr_pins: An alternate set of address pins to use. Defaults to None
    :param string color_order: A string containing the letter "R", "G", and "B" in the
                               order you want. Defaults to "RGB"
    :param debug: Turn on debug print outs. Defaults to False.
    :param int width: The total width of the display(s) in Pixels. Defaults to 64.
    :param int height: The total height of the display(s) in Pixels. Defaults to 32.
    :param bool Serpentine: Used when panels are arranged in a serpentine pattern rather
                            than a Z-pattern. Defaults to True.
    :param int tiles_rows: Used to indicate the number of rows the panels are arranged in.
                           Defaults to 1.

    """

    # pylint: disable=too-many-locals
    def __init__(
        self,
        *,
        url=None,
        headers=None,
        json_path=None,
        regexp_path=None,
        default_bg=0x000000,
        status_neopixel=None,
        json_transform=None,
        esp=None,
        external_spi=None,
        bit_depth=2,
        alt_addr_pins=None,
        color_order="RGB",
        debug=False,
        width=64,
        height=32,
        serpentine=True,
        tile_rows=1,
    ):

        graphics = Graphics(
            default_bg=default_bg,
            bit_depth=bit_depth,
            width=width,
            height=height,
            alt_addr_pins=alt_addr_pins,
            color_order=color_order,
            serpentine=serpentine,
            tile_rows=tile_rows,
            debug=debug,
        )

        network = Network(
            status_neopixel=status_neopixel,
            esp=esp,
            external_spi=external_spi,
            extract_values=False,
            debug=debug,
        )

        super().__init__(
            network,
            graphics,
            url=url,
            headers=headers,
            json_path=json_path,
            regexp_path=regexp_path,
            json_transform=json_transform,
            debug=debug,
        )

        self._scrolling_index = None

        gc.collect()

    # pylint: disable=too-many-arguments, arguments-differ
    def add_text(
        self,
        text_position=None,
        text_font=terminalio.FONT,
        text_color=0x808080,
        text_wrap=False,
        text_maxlen=0,
        text_transform=None,
        text_scale=1,
        scrolling=False,
        line_spacing=1.25,
        text_anchor_point=(0, 0.5),
        is_data=True,
    ):
        """
        Add text labels with settings

        :param str text_font: The path to your font file for your data text display.
        :param text_position: The position of your extracted text on the display in an (x, y) tuple.
                              Can be a list of tuples for when there's a list of json_paths, for
                              example.
        :param text_color: The color of the text, in 0xRRGGBB format. Can be a list of colors for
                           when there's multiple texts. Defaults to ``None``.
        :param text_wrap: Whether or not to wrap text (for long text data chunks). Defaults to
                          ``False``, no wrapping.
        :param text_maxlen: The max length of the text for text wrapping. Defaults to 0.
        :param text_transform: A function that will be called on the text before display
        :param int text_scale: The factor to scale the default size of the text by
        :param bool scrolling: If true, text is placed offscreen and the scroll() function is used
                               to scroll text on a pixel-by-pixel basis. Multiple text labels with
                               the scrolling set to True will be cycled through.
        :param (float, float) text_anchor_point: Values between 0 and 1 to indicate where the text
                                                 position is relative to the label
        :param bool is_data: If True, fetch will attempt to update the label
        """
        if scrolling:
            if text_position is None:
                # Center text if position not specified
                text_position = (self.display.width, self.display.height // 2 - 1)
            else:
                text_position = (self.display.width, text_position[1])

        index = super().add_text(
            text_position=text_position,
            text_font=text_font,
            text_color=text_color,
            text_wrap=text_wrap,
            text_maxlen=text_maxlen,
            text_transform=text_transform,
            text_scale=text_scale,
            line_spacing=line_spacing,
            text_anchor_point=text_anchor_point,
            is_data=is_data,
        )

        self._text[index]["scrolling"] = scrolling

        if scrolling and self._scrolling_index is None:  # Not initialized yet
            self._scrolling_index = self._get_next_scrollable_text_index()

        return index

    # pylint: enable=too-many-arguments, arguments-differ

    def set_background(self, file_or_color, position=None):
        """The background image to a bitmap file.

        :param file_or_color: The filename of the chosen background image, or a hex color.

        """
        self.graphics.set_background(file_or_color, position)

    def _get_next_scrollable_text_index(self):
        index = self._scrolling_index
        while True:
            if index is None:
                index = 0
            else:
                index += 1
            if index >= len(self._text):
                index = 0
            if self._text[index]["scrolling"]:
                return index
            if index == self._scrolling_index:
                return None

    def scroll(self):
        """Scroll any text that needs scrolling by a single frame. We also
        we want to queue up multiple lines one after another. To get
        simultaneous lines, we can simply use a line break.
        """

        if self._scrolling_index is None:  # Not initialized yet
            return

        self._text[self._scrolling_index]["label"].x = (
            self._text[self._scrolling_index]["label"].x - 1
        )
        line_width = (
            self._text[self._scrolling_index]["label"].bounding_box[2]
            * self._text[self._scrolling_index]["scale"]
        )
        if self._text[self._scrolling_index]["label"].x < -line_width:
            # Find the next line
            self._scrolling_index = self._get_next_scrollable_text_index()
            self._text[self._scrolling_index]["label"].x = self.graphics.display.width

    def scroll_text(self, frame_delay=0.02):
        """Scroll the entire text all the way across. We also
        we want to queue up multiple lines one after another. To get
        simultaneous lines, we can simply use a line break.
        """
        if self._scrolling_index is None:  # Not initialized yet
            return
        if self._text[self._scrolling_index]["label"] is not None:
            self._text[self._scrolling_index]["label"].x = self.graphics.display.width
            line_width = (
                self._text[self._scrolling_index]["label"].bounding_box[2]
                * self._text[self._scrolling_index]["scale"]
            )
            for _ in range(self.graphics.display.width + line_width + 1):
                self.scroll()
                sleep(frame_delay)
        else:
            raise RuntimeError(
                "Please assign text to the label with index {} before scrolling".format(
                    self._scrolling_index
                )
            )
