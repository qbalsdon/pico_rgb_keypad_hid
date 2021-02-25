# SPDX-FileCopyrightText: 2017 Scott Shawcroft, written for Adafruit Industries
# SPDX-FileCopyrightText: Copyright (c) 2020 Melissa LeBlanc-Williams for Adafruit Industries
#
# SPDX-License-Identifier: MIT
"""
`adafruit_portalbase`
================================================================================

Base Library for the Portal-style libraries.


* Author(s): Melissa LeBlanc-Williams

Implementation Notes
--------------------

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://github.com/adafruit/circuitpython/releases

"""
import gc
import time
import terminalio
from adafruit_bitmap_font import bitmap_font
from adafruit_display_text.label import Label
from adafruit_display_text import wrap_text_to_lines

__version__ = "1.2.2"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_PortalBase.git"


class PortalBase:
    """Class representing the Adafruit MagTag.

    :param network: An initialized network class instance.
    :param graphics: An initialized graphics class instance.
    :param url: The URL of your data source. Defaults to ``None``.
    :param headers: The headers for authentication, typically used by Azure API's.
    :param json_path: The list of json traversal to get data out of. Can be list of lists for
                    multiple data points. Defaults to ``None`` to not use json.
    :param regexp_path: The list of regexp strings to get data out (use a single regexp group).
                        Can be list of regexps for multiple data points. Defaults to ``None``
                        to not use regexp.
    :param default_bg: The path to your default background image file or a hex color.
                    Defaults to 0x000000.
    :param status_neopixel: The pin for the status NeoPixel. Use ``board.NEOPIXEL`` for the
                            on-board NeoPixel. Defaults to ``None``, to not use the status LED
    :param json_transform: A function or a list of functions to call with the parsed JSON.
                        Changes and additions are permitted for the ``dict`` object.
    :param success_callback: A function we'll call if you like, when we fetch data successfully.
                             Defaults to ``None``.
    :param debug: Turn on debug print outs. Defaults to False.

    """

    # pylint: disable=too-many-instance-attributes, too-many-branches
    def __init__(
        self,
        network,
        graphics,
        *,
        url=None,
        headers=None,
        json_path=None,
        regexp_path=None,
        json_transform=None,
        success_callback=None,
        debug=False,
    ):
        self.network = network
        self.graphics = graphics
        self.splash = self.graphics.splash
        self.display = self.graphics.display

        # Font Cache
        self._fonts = {}
        self._text = []

        try:
            import alarm  # pylint: disable=import-outside-toplevel

            self._alarm = alarm
        except ImportError:
            self._alarm = None
        self._debug = debug
        self.url = url
        self._headers = headers
        self._json_path = None
        self.json_path = json_path

        self._regexp_path = regexp_path
        self._success_callback = success_callback

        # Add any JSON translators
        if json_transform:
            self.network.add_json_transform(json_transform)

    def _load_font(self, font):
        """
        Load and cache a font if not previously loaded
        Return the key of the cached font

        :param font: Either terminalio.FONT or the path to the bdf font file

        """
        if font is terminalio.FONT:
            if "terminal" not in self._fonts:
                self._fonts["terminal"] = terminalio.FONT
            return "terminal"
        if font not in self._fonts:
            self._fonts[font] = bitmap_font.load_font(font)
        return font

    @staticmethod
    def html_color_convert(color):
        """Convert an HTML color code to an integer

        :param color: The color value to be converted

        """
        if isinstance(color, str):
            if color[0] == "#":
                color = color.lstrip("#")
            return int(color, 16)
        return color  # Return unconverted

    @staticmethod
    def wrap_nicely(string, max_chars):
        """A helper that will return a list of lines with word-break wrapping.

        :param str string: The text to be wrapped.
        :param int max_chars: The maximum number of characters on a line before wrapping.

        """
        return wrap_text_to_lines(string, max_chars)

    # pylint: disable=too-many-arguments
    def add_text(
        self,
        text_position=(0, 0),
        text_font=terminalio.FONT,
        text_color=0x000000,
        text_wrap=0,
        text_maxlen=0,
        text_transform=None,
        text_scale=1,
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
        :param text_wrap: When non-zero, the maximum number of characters on each line before text
                          is wrapped. (for long text data chunks). Defaults to 0, no wrapping.
        :param text_maxlen: The max length of the text. If non-zero, it will be truncated to this
                            length. Defaults to 0.
        :param text_transform: A function that will be called on the text before display
        :param int text_scale: The factor to scale the default size of the text by
        :param float line_spacing: The factor to space the lines apart
        :param (float, float) text_anchor_point: Values between 0 and 1 to indicate where the text
                                                 position is relative to the label
        :param bool is_data: If True, fetch will attempt to update the label
        """
        if not text_wrap:
            text_wrap = 0
        if not text_maxlen:
            text_maxlen = 0
        if not text_transform:
            text_transform = None
        if not isinstance(text_scale, (int, float)) or text_scale < 1:
            text_scale = 1
        if not isinstance(text_anchor_point, (tuple, list)):
            text_anchor_point = (0, 0.5)
        if not 0 <= text_anchor_point[0] <= 1 or not 0 <= text_anchor_point[1] <= 1:
            raise ValueError("Text anchor point values should be between 0 and 1.")
        text_scale = round(text_scale)
        gc.collect()

        if self._debug:
            print("Init text area")
        text_field = {
            "label": None,
            "font": self._load_font(text_font),
            "color": self.html_color_convert(text_color),
            "position": text_position,
            "wrap": text_wrap,
            "maxlen": text_maxlen,
            "transform": text_transform,
            "scale": text_scale,
            "line_spacing": line_spacing,
            "anchor_point": text_anchor_point,
            "is_data": bool(is_data),
        }
        self._text.append(text_field)

        return len(self._text) - 1

    # pylint: enable=too-many-arguments

    def set_text(self, val, index=0):
        """Display text, with indexing into our list of text boxes.

        :param str val: The text to be displayed
        :param index: Defaults to 0.

        """
        # Make sure at least a single label exists
        if not self._text:
            self.add_text()
        string = str(val)
        if self._text[index]["maxlen"]:
            if len(string) >= 3:
                # too long! shorten it
                string = string[: self._text[index]["maxlen"] - 3] + "..."
            else:
                string = string[: self._text[index]["maxlen"]]
        index_in_splash = None

        if len(string) > 0 and self._text[index]["wrap"]:
            if self._debug:
                print("Wrapping text with length of", self._text[index]["wrap"])
            lines = self.wrap_nicely(string, self._text[index]["wrap"])
            string = "\n".join(lines)

        if self._text[index]["label"] is not None:
            if self._debug:
                print("Replacing text area with :", string)
            index_in_splash = self.splash.index(self._text[index]["label"])
        elif self._debug:
            print("Creating text area with :", string)

        if len(string) > 0:
            self._text[index]["label"] = Label(
                self._fonts[self._text[index]["font"]],
                text=string,
                scale=self._text[index]["scale"],
            )
            self._text[index]["label"].color = self._text[index]["color"]
            self._text[index]["label"].anchor_point = self._text[index]["anchor_point"]
            self._text[index]["label"].anchored_position = self._text[index]["position"]
            self._text[index]["label"].line_spacing = self._text[index]["line_spacing"]
        elif index_in_splash is not None:
            self._text[index]["label"] = None

        if index_in_splash is not None:
            if self._text[index]["label"] is not None:
                self.splash[index_in_splash] = self._text[index]["label"]
            else:
                del self.splash[index_in_splash]
        elif self._text[index]["label"] is not None:
            self.splash.append(self._text[index]["label"])

    def preload_font(self, glyphs=None, index=0):
        # pylint: disable=line-too-long
        """Preload font.

        :param glyphs: The font glyphs to load. Defaults to ``None``, uses alphanumeric glyphs if
                       None.
        """
        # pylint: enable=line-too-long
        if not glyphs:
            glyphs = b"0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ-!,. \"'?!"
        print("Preloading font glyphs:", glyphs)
        if self._fonts[self._text[index]["font"]] is not terminalio.FONT:
            self._fonts[self._text[index]["font"]].load_glyphs(glyphs)

    def set_headers(self, headers):
        """Set the headers used by fetch().

        :param headers: The new header dictionary

        """
        self._headers = headers

    def set_background(self, file_or_color, position=None):
        """The background image to a bitmap file.

        :param file_or_color: The filename of the chosen background image, or a hex color.

        """
        self.graphics.set_background(file_or_color, position)

    def set_text_color(self, color, index=0):
        """Update the text color, with indexing into our list of text boxes.

        :param int color: The color value to be used
        :param index: Defaults to 0.

        """
        if self._text[index]:
            color = self.html_color_convert(color)
            self._text[index]["color"] = color
            self._text[index]["label"].color = color

    def exit_and_deep_sleep(self, sleep_time):
        """
        Stops the current program and enters deep sleep. The program is restarted from the beginning
        after a certain period of time.

        See https://circuitpython.readthedocs.io/en/latest/shared-bindings/alarm/index.html for more
        details.

        :param float sleep_time: The amount of time to sleep in seconds

        """
        if self._alarm:
            pause = self._alarm.time.TimeAlarm(
                monotonic_time=time.monotonic() + sleep_time
            )
            self._alarm.exit_and_deep_sleep_until_alarms(pause)
        else:
            raise NotImplementedError(
                "Deep sleep not supported. Make sure you have the latest CircuitPython."
            )

    def enter_light_sleep(self, sleep_time):
        """
        Enter light sleep and resume the program after a certain period of time.

        See https://circuitpython.readthedocs.io/en/latest/shared-bindings/alarm/index.html for more
        details.

        :param float sleep_time: The amount of time to sleep in seconds

        """
        if self._alarm:
            pause = self._alarm.time.TimeAlarm(
                monotonic_time=time.monotonic() + sleep_time
            )
            self._alarm.light_sleep_until_alarms(pause)
        else:
            raise NotImplementedError(
                "Hardware light sleep not supported. Make sure you have the latest CircuitPython."
            )

    def _fetch_set_text(self, val, index=0):
        self.set_text(val, index=index)

    def fetch(self, refresh_url=None, timeout=10):
        """Fetch data from the url we initialized with, perfom any parsing,
        and display text or graphics. This function does pretty much everything
        Optionally update the URL

        :param str refresh_url: The overriding URL to fetch from. Defaults to ``None``.
        :param int timeout: The timeout period in seconds.

        """
        if refresh_url:
            self.url = refresh_url
        values = []

        values = self.network.fetch_data(
            self.url,
            headers=self._headers,
            json_path=self._json_path,
            regexp_path=self._regexp_path,
            timeout=timeout,
        )

        # if we have a callback registered, call it now
        if self._success_callback:
            self._success_callback(values)

        self._fill_text_labels(values)

        if len(values) == 1:
            return values[0]
        return values

    def _fill_text_labels(self, values):
        # fill out all the text blocks
        if self._text:
            value_index = 0  # In case values and text is not the same
            for i in range(len(self._text)):
                if not self._text[i]["is_data"]:
                    continue
                string = None
                if self._text[i]["transform"]:
                    func = self._text[i]["transform"]
                    string = func(values[value_index])
                else:
                    try:
                        string = "{:,d}".format(int(values[value_index]))
                    except (TypeError, ValueError):
                        string = values[value_index]  # ok it's a string
                self._fetch_set_text(string, index=i)
                value_index += 1

    def get_local_time(self, location=None):
        """Accessor function for get_local_time()"""
        return self.network.get_local_time(location=location)

    def push_to_io(self, feed_key, data):
        """Push data to an adafruit.io feed

        :param str feed_key: Name of feed key to push data to.
        :param data: data to send to feed

        """

        self.network.push_to_io(feed_key, data)

    def get_io_data(self, feed_key):
        """Return all values from the Adafruit IO Feed Data that matches the feed key

        :param str feed_key: Name of feed key to receive data from.

        """

        return self.network.get_io_data(feed_key)

    def get_io_feed(self, feed_key, detailed=False):
        """Return the Adafruit IO Feed that matches the feed key

        :param str feed_key: Name of feed key to match.
        :param bool detailed: Whether to return additional detailed information

        """
        return self.network.get_io_feed(feed_key, detailed)

    def get_io_group(self, group_key):
        """Return the Adafruit IO Group that matches the group key

        :param str group_key: Name of group key to match.

        """
        return self.network.get_io_group(group_key)

    @property
    def json_path(self):
        """
        Get or set the list of json traversal to get data out of. Can be list
        of lists for multiple data points.
        """
        return self._json_path

    @json_path.setter
    def json_path(self, value):
        if value:
            if isinstance(value[0], (list, tuple)):
                self._json_path = value
            else:
                self._json_path = (value,)
        else:
            self._json_path = None
