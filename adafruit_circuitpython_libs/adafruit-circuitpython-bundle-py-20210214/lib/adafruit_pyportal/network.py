# SPDX-FileCopyrightText: 2020 Melissa LeBlanc-Williams, written for Adafruit Industries
#
# SPDX-License-Identifier: Unlicense
"""
`adafruit_pyportal.network`
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

import gc

# pylint: disable=unused-import
from adafruit_portalbase.network import (
    NetworkBase,
    CONTENT_JSON,
    CONTENT_TEXT,
)

# pylint: enable=unused-import
from adafruit_pyportal.wifi import WiFi

__version__ = "5.1.3"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_PyPortal.git"

# you'll need to pass in an io username, width, height, format (bit depth), io key, and then url!
IMAGE_CONVERTER_SERVICE = (
    "https://io.adafruit.com/api/v2/%s/integrations/image-formatter?"
    "x-aio-key=%s&width=%d&height=%d&output=BMP%d&url=%s"
)


class Network(NetworkBase):
    """Class representing the Adafruit PyPortal.

    :param status_neopixel: The pin for the status NeoPixel. Use ``board.NEOPIXEL`` for the on-board
                            NeoPixel. Defaults to ``None``, not the status LED
    :param esp: A passed ESP32 object, Can be used in cases where the ESP32 chip needs to be used
                             before calling the pyportal class. Defaults to ``None``.
    :param busio.SPI external_spi: A previously declared spi object. Defaults to ``None``.
    :param bool extract_values: If true, single-length fetched values are automatically extracted
                                from lists and tuples. Defaults to ``True``.
    :param debug: Turn on debug print outs. Defaults to False.
    :param convert_image: Determine whether or not to use the AdafruitIO image converter service.
                          Set as False if your image is already resized. Defaults to True.
    :param image_url_path: The HTTP traversal path for a background image to display.
                             Defaults to ``None``.
    :param image_json_path: The JSON traversal path for a background image to display. Defaults to
                            ``None``.
    :param image_resize: What size to resize the image we got from the json_path, make this a tuple
                         of the width and height you want. Defaults to ``None``.
    :param image_position: The position of the image on the display as an (x, y) tuple. Defaults to
                           ``None``.
    :param image_dim_json_path: The JSON traversal path for the original dimensions of image tuple.
                                Used with fetch(). Defaults to ``None``.

    """

    def __init__(
        self,
        *,
        status_neopixel=None,
        esp=None,
        external_spi=None,
        extract_values=True,
        debug=False,
        convert_image=True,
        image_url_path=None,
        image_json_path=None,
        image_resize=None,
        image_position=None,
        image_dim_json_path=None,
        secrets_data=None,
    ):
        wifi = WiFi(status_neopixel=status_neopixel, esp=esp, external_spi=external_spi)

        super().__init__(
            wifi,
            extract_values=extract_values,
            debug=debug,
            secrets_data=secrets_data,
        )

        self._convert_image = convert_image
        self._image_json_path = image_json_path
        self._image_url_path = image_url_path
        self._image_resize = image_resize
        self._image_position = image_position
        self._image_dim_json_path = image_dim_json_path
        gc.collect()

    @property
    def ip_address(self):
        """Return the IP Address nicely formatted"""
        return self._wifi.esp.pretty_ip(self._wifi.esp.ip_address)

    def image_converter_url(self, image_url, width, height, color_depth=16):
        """Generate a converted image url from the url passed in,
        with the given width and height. aio_username and aio_key must be
        set in secrets."""
        try:
            aio_username = self._secrets["aio_username"]
            aio_key = self._secrets["aio_key"]
        except KeyError as error:
            raise KeyError(
                "\n\nOur image converter service require a login/password to rate-limit. Please register for a free adafruit.io account and place the user/key in your secrets file under 'aio_username' and 'aio_key'"  # pylint: disable=line-too-long
            ) from error

        return IMAGE_CONVERTER_SERVICE % (
            aio_username,
            aio_key,
            width,
            height,
            color_depth,
            image_url,
        )

    # pylint: disable=too-many-branches, too-many-statements
    def process_image(self, json_data, sd_card=False):
        """
        Process image content

        :param json_data: The JSON data that we can pluck values from
        :param bool sd_card: Whether or not we have an SD card inserted

        """
        filename = None
        position = None
        image_url = None

        if self._image_url_path:
            image_url = self._image_url_path

        if self._image_json_path:
            image_url = self.json_traverse(json_data, self._image_json_path)

        iwidth = 0
        iheight = 0
        if self._image_dim_json_path:
            iwidth = int(self.json_traverse(json_data, self._image_dim_json_path[0]))
            iheight = int(self.json_traverse(json_data, self._image_dim_json_path[1]))
            print("image dim:", iwidth, iheight)

        if image_url:
            print("original URL:", image_url)
            if self._convert_image:
                if iwidth < iheight:
                    image_url = self.image_converter_url(
                        image_url,
                        int(
                            self._image_resize[1]
                            * self._image_resize[1]
                            / self._image_resize[0]
                        ),
                        self._image_resize[1],
                    )
                else:
                    image_url = self.image_converter_url(
                        image_url, self._image_resize[0], self._image_resize[1]
                    )

                print("convert URL:", image_url)
            # convert image to bitmap and cache
            # print("**not actually wgetting**")
            filename = "/cache.bmp"
            chunk_size = 4096  # default chunk size is 12K (for QSPI)
            if sd_card:
                filename = "/sd" + filename
                chunk_size = 512  # current bug in big SD writes -> stick to 1 block
            try:
                self.wget(image_url, filename, chunk_size=chunk_size)
            except OSError as error:
                raise OSError(
                    """\n\nNo writable filesystem found for saving datastream. Insert an SD card or set internal filesystem to be unsafe by setting 'disable_concurrent_write_protection' in the mount options in boot.py"""  # pylint: disable=line-too-long
                ) from error
            except RuntimeError as error:
                raise RuntimeError("wget didn't write a complete file") from error
            if iwidth < iheight:
                pwidth = int(
                    self._image_resize[1]
                    * self._image_resize[1]
                    / self._image_resize[0]
                )
                position = (
                    self._image_position[0] + int((self._image_resize[0] - pwidth) / 2),
                    self._image_position[1],
                )
            else:
                position = self._image_position

            image_url = None
            gc.collect()

        return filename, position
