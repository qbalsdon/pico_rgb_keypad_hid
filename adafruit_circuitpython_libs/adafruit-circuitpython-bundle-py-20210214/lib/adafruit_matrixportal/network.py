# SPDX-FileCopyrightText: 2020 Melissa LeBlanc-Williams, written for Adafruit Industries
#
# SPDX-License-Identifier: Unlicense
"""
`adafruit_matrixportal.network`
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
from adafruit_portalbase.network import NetworkBase
from adafruit_matrixportal.wifi import WiFi

__version__ = "2.1.0"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_MatrixPortal.git"


class Network(NetworkBase):
    """Class representing the Adafruit RGB Matrix Portal.

    :param status_neopixel: The pin for the status NeoPixel. Use ``board.NEOPIXEL`` for the on-board
                            NeoPixel. Defaults to ``None``, not the status LED
    :param esp: A passed ESP32 object, Can be used in cases where the ESP32 chip needs to be used
                             before calling the pyportal class. Defaults to ``None``.
    :param busio.SPI external_spi: A previously declared spi object. Defaults to ``None``.
    :param bool extract_values: If true, single-length fetched values are automatically extracted
                                from lists and tuples. Defaults to ``True``.
    :param debug: Turn on debug print outs. Defaults to False.

    """

    def __init__(
        self,
        *,
        status_neopixel=None,
        esp=None,
        external_spi=None,
        extract_values=True,
        debug=False,
    ):
        wifi = WiFi(status_neopixel=status_neopixel, esp=esp, external_spi=external_spi)

        super().__init__(
            wifi, extract_values=extract_values, debug=debug,
        )

        gc.collect()

    @property
    def ip_address(self):
        """Return the IP Address nicely formatted"""
        return self._wifi.esp.pretty_ip(self._wifi.esp.ip_address)
