# SPDX-FileCopyrightText: 2020 Melissa LeBlanc-Williams, written for Adafruit Industries
#
# SPDX-License-Identifier: Unlicense
"""
`adafruit_pyportal`
================================================================================

CircuitPython driver for Adafruit PyPortal.

* Author(s): Limor Fried, Kevin J. Walters, Melissa LeBlanc-Williams

Implementation Notes
--------------------

**Hardware:**

* `Adafruit PyPortal <https://www.adafruit.com/product/4116>`_

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://github.com/adafruit/circuitpython/releases

"""

import os
import gc
import time
import board
import terminalio
import supervisor
from adafruit_portalbase import PortalBase
from adafruit_pyportal.network import Network, CONTENT_JSON, CONTENT_TEXT
from adafruit_pyportal.graphics import Graphics
from adafruit_pyportal.peripherals import Peripherals

__version__ = "5.1.3"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_PyPortal.git"


class PyPortal(PortalBase):
    """Class representing the Adafruit PyPortal.

    :param url: The URL of your data source. Defaults to ``None``.
    :param headers: The headers for authentication, typically used by Azure API's.
    :param json_path: The list of json traversal to get data out of. Can be list of lists for
                      multiple data points. Defaults to ``None`` to not use json.
    :param regexp_path: The list of regexp strings to get data out (use a single regexp group). Can
                        be list of regexps for multiple data points. Defaults to ``None`` to not
                        use regexp.
    :param convert_image: Determine whether or not to use the AdafruitIO image converter service.
                          Set as False if your image is already resized. Defaults to True.
    :param default_bg: The path to your default background image file or a hex color.
                       Defaults to 0x000000.
    :param status_neopixel: The pin for the status NeoPixel. Use ``board.NEOPIXEL`` for the on-board
                            NeoPixel. Defaults to ``None``, not the status LED
    :param str text_font: The path to your font file for your data text display.
    :param text_position: The position of your extracted text on the display in an (x, y) tuple.
                          Can be a list of tuples for when there's a list of json_paths, for example
    :param text_color: The color of the text, in 0xRRGGBB format. Can be a list of colors for when
                       there's multiple texts. Defaults to ``None``.
    :param text_wrap: Whether or not to wrap text (for long text data chunks). Defaults to
                      ``False``, no wrapping.
    :param text_maxlen: The max length of the text for text wrapping. Defaults to 0.
    :param text_transform: A function that will be called on the text before display
    :param int text_scale: The factor to scale the default size of the text by
    :param json_transform: A function or a list of functions to call with the parsed JSON.
                           Changes and additions are permitted for the ``dict`` object.
    :param image_json_path: The JSON traversal path for a background image to display. Defaults to
                            ``None``.
    :param image_resize: What size to resize the image we got from the json_path, make this a tuple
                         of the width and height you want. Defaults to ``None``.
    :param image_position: The position of the image on the display as an (x, y) tuple. Defaults to
                           ``None``.
    :param image_dim_json_path: The JSON traversal path for the original dimensions of image tuple.
                                Used with fetch(). Defaults to ``None``.
    :param success_callback: A function we'll call if you like, when we fetch data successfully.
                             Defaults to ``None``.
    :param str caption_text: The text of your caption, a fixed text not changed by the data we get.
                             Defaults to ``None``.
    :param str caption_font: The path to the font file for your caption. Defaults to ``None``.
    :param caption_position: The position of your caption on the display as an (x, y) tuple.
                             Defaults to ``None``.
    :param caption_color: The color of your caption. Must be a hex value, e.g. ``0x808000``.
    :param image_url_path: The HTTP traversal path for a background image to display.
                             Defaults to ``None``.
    :param esp: A passed ESP32 object, Can be used in cases where the ESP32 chip needs to be used
                             before calling the pyportal class. Defaults to ``None``.
    :param busio.SPI external_spi: A previously declared spi object. Defaults to ``None``.
    :param debug: Turn on debug print outs. Defaults to False.

    """

    # pylint: disable=too-many-instance-attributes, too-many-locals, too-many-branches, too-many-statements
    def __init__(
        self,
        *,
        url=None,
        headers=None,
        json_path=None,
        regexp_path=None,
        convert_image=True,
        default_bg=0x000000,
        status_neopixel=None,
        text_font=terminalio.FONT,
        text_position=None,
        text_color=0x808080,
        text_wrap=False,
        text_maxlen=0,
        text_transform=None,
        text_scale=1,
        json_transform=None,
        image_json_path=None,
        image_resize=None,
        image_position=None,
        image_dim_json_path=None,
        caption_text=None,
        caption_font=None,
        caption_position=None,
        caption_color=0x808080,
        image_url_path=None,
        success_callback=None,
        esp=None,
        external_spi=None,
        debug=False,
        secrets_data=None,
    ):

        graphics = Graphics(
            default_bg=default_bg,
            debug=debug,
        )

        self._default_bg = default_bg

        if external_spi:  # If SPI Object Passed
            spi = external_spi
        else:  # Else: Make ESP32 connection
            spi = board.SPI()

        if image_json_path or image_url_path:
            if debug:
                print("Init image path")
            if not image_position:
                image_position = (0, 0)  # default to top corner
            if not image_resize:
                image_resize = (
                    self.display.width,
                    self.display.height,
                )  # default to full screen

        network = Network(
            status_neopixel=status_neopixel,
            esp=esp,
            external_spi=spi,
            extract_values=False,
            convert_image=convert_image,
            image_url_path=image_url_path,
            image_json_path=image_json_path,
            image_resize=image_resize,
            image_position=image_position,
            image_dim_json_path=image_dim_json_path,
            debug=debug,
            secrets_data=secrets_data,
        )

        self.url = url

        super().__init__(
            network,
            graphics,
            url=url,
            headers=headers,
            json_path=json_path,
            regexp_path=regexp_path,
            json_transform=json_transform,
            success_callback=success_callback,
            debug=debug,
        )

        # Convenience Shortcuts for compatibility
        self.peripherals = Peripherals(
            spi, display=self.display, splash_group=self.splash, debug=debug
        )
        self.set_backlight = self.peripherals.set_backlight
        self.sd_check = self.peripherals.sd_check
        self.play_file = self.peripherals.play_file

        self.image_converter_url = self.network.image_converter_url
        self.wget = self.network.wget
        # pylint: disable=invalid-name
        self.show_QR = self.graphics.qrcode
        self.hide_QR = self.graphics.hide_QR
        # pylint: enable=invalid-name

        if hasattr(self.peripherals, "touchscreen"):
            self.touchscreen = self.peripherals.touchscreen
        if hasattr(self.peripherals, "mouse_cursor"):
            self.mouse_cursor = self.peripherals.mouse_cursor
        if hasattr(self.peripherals, "cursor"):
            self.cursor = self.peripherals.cursor

        # show thank you and bootup file if available
        for bootscreen in ("/thankyou.bmp", "/pyportal_startup.bmp"):
            try:
                os.stat(bootscreen)
                for i in range(100, -1, -1):  # dim down
                    self.set_backlight(i / 100)
                    time.sleep(0.005)
                self.set_background(bootscreen)
                try:
                    self.display.refresh(target_frames_per_second=60)
                except AttributeError:
                    self.display.wait_for_frame()
                for i in range(100):  # dim up
                    self.set_backlight(i / 100)
                    time.sleep(0.005)
                time.sleep(2)
            except OSError:
                pass  # they removed it, skip!

        try:
            self.peripherals.play_file("pyportal_startup.wav")
        except OSError:
            pass  # they deleted the file, no biggie!

        if default_bg is not None:
            self.graphics.set_background(default_bg)

        if self._debug:
            print("Init caption")
        if caption_font:
            self._caption_font = self._load_font(caption_font)
        self.set_caption(caption_text, caption_position, caption_color)

        if text_font:
            if text_position is not None and isinstance(
                text_position[0], (list, tuple)
            ):
                num = len(text_position)
                if not text_wrap:
                    text_wrap = [0] * num
                if not text_maxlen:
                    text_maxlen = [0] * num
                if not text_transform:
                    text_transform = [None] * num
                if not isinstance(text_scale, (list, tuple)):
                    text_scale = [text_scale] * num
            else:
                num = 1
                text_position = (text_position,)
                text_color = (text_color,)
                text_wrap = (text_wrap,)
                text_maxlen = (text_maxlen,)
                text_transform = (text_transform,)
                text_scale = (text_scale,)
            for i in range(num):
                self.add_text(
                    text_position=text_position[i],
                    text_font=text_font,
                    text_color=text_color[i],
                    text_wrap=text_wrap[i],
                    text_maxlen=text_maxlen[i],
                    text_transform=text_transform[i],
                    text_scale=text_scale[i],
                )
        else:
            self._text_font = None
            self._text = None

        gc.collect()

    def set_caption(self, caption_text, caption_position, caption_color):
        # pylint: disable=line-too-long
        """A caption. Requires setting ``caption_font`` in init!

        :param caption_text: The text of the caption.
        :param caption_position: The position of the caption text.
        :param caption_color: The color of your caption text. Must be a hex value, e.g.
                              ``0x808000``.
        """
        # pylint: enable=line-too-long
        if self._debug:
            print("Setting caption to", caption_text)

        if (not caption_text) or (not self._caption_font) or (not caption_position):
            return  # nothing to do!

        index = self.add_text(
            text_position=caption_position,
            text_font=self._caption_font,
            text_color=caption_color,
            is_data=False,
        )
        self.set_text(caption_text, index)

    def fetch(self, refresh_url=None, timeout=10):
        """Fetch data from the url we initialized with, perfom any parsing,
        and display text or graphics. This function does pretty much everything
        Optionally update the URL
        """

        if refresh_url:
            self.url = refresh_url

        response = self.network.fetch(self.url, timeout=timeout)

        json_out = None
        content_type = self.network.check_response(response)
        json_path = self._json_path

        if content_type == CONTENT_JSON:
            if json_path is not None:
                # Drill down to the json path and set json_out as that node
                if isinstance(json_path, (list, tuple)) and (
                    not json_path or not isinstance(json_path[0], (list, tuple))
                ):
                    json_path = (json_path,)
            try:
                gc.collect()
                json_out = response.json()
                if self._debug:
                    print(json_out)
                gc.collect()
            except ValueError:  # failed to parse?
                print("Couldn't parse json: ", response.text)
                raise
            except MemoryError:
                supervisor.reload()

        try:
            filename, position = self.network.process_image(
                json_out, self.peripherals.sd_check()
            )
            if filename and position is not None:
                self.graphics.set_background(filename, position)
        except ValueError as error:
            print("Error displaying cached image. " + error.args[0])
            if self._default_bg is not None:
                self.graphics.set_background(self._default_bg)
        except KeyError as error:
            print("Error finding image data. '" + error.args[0] + "' not found.")
            self.set_background(self._default_bg)

        if content_type == CONTENT_JSON:
            values = self.network.process_json(json_out, json_path)
        elif content_type == CONTENT_TEXT:
            values = self.network.process_text(response.text, self._regexp_path)

        # if we have a callback registered, call it now
        if self._success_callback:
            self._success_callback(values)

        self._fill_text_labels(values)
        # Clean up
        json_out = None
        response = None
        gc.collect()

        if len(values) == 1:
            values = values[0]

        return values
