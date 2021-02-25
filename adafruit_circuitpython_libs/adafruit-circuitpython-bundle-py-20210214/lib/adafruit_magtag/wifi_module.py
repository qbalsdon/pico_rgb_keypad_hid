# SPDX-FileCopyrightText: 2017 Scott Shawcroft, written for Adafruit Industries
# SPDX-FileCopyrightText: Copyright (c) 2020 Melissa LeBlanc-Williams for Adafruit Industries
#
# SPDX-License-Identifier: MIT
"""
`adafruit_magtag.wifi_module`
================================================================================

Helper Library for the Adafruit MagTag.


* Author(s): Melissa LeBlanc-Williams

Implementation Notes
--------------------

**Hardware:**

* `Adafruit MagTag <https://www.adafruit.com/product/4800>`_

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://github.com/adafruit/circuitpython/releases

* Adafruit's PortalBase library: https://github.com/adafruit/Adafruit_CircuitPython_PortalBase

"""

import gc
import ssl
import neopixel
import wifi
import socketpool
import adafruit_requests

__version__ = "1.6.0"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_MagTag.git"


class WiFi:
    """Class representing the WiFi portion of the ESP32-S2.

    :param status_neopixel: The pin for the status NeoPixel. Use ``board.NEOPIXEL`` for the on-board
                            NeoPixel. Defaults to ``None``, not the status LED

    """

    def __init__(self, *, status_neopixel=None):

        if status_neopixel:
            self.neopix = neopixel.NeoPixel(status_neopixel, 1, brightness=0.2)
        else:
            self.neopix = None
        self.neo_status(0)
        self.requests = None
        self._connected = False

        gc.collect()

    def connect(self, ssid, password):
        """
        Connect to the WiFi Network using the information provided

        :param ssid: The WiFi name
        :param password: The WiFi password

        """
        wifi.radio.connect(ssid, password)
        pool = socketpool.SocketPool(wifi.radio)
        self.requests = adafruit_requests.Session(pool, ssl.create_default_context())
        self._connected = True

    def neo_status(self, value):
        """The status NeoPixel.

        :param value: The color to change the NeoPixel.

        """
        if self.neopix:
            self.neopix.fill(value)

    @property
    def is_connected(self):
        """
        Return whether we have already connected since reconnections are handled automatically.

        """
        return self._connected

    @property
    def ip_address(self):
        """
        Return the IP Version 4 Address

        """
        return wifi.radio.ipv4_address

    @property
    def enabled(self):
        """
        Return whether the WiFi Radio is enabled

        """
        return wifi.radio.enabled
