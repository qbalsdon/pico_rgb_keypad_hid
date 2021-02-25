# SPDX-FileCopyrightText: 2020 Melissa LeBlanc-Williams, written for Adafruit Industries
#
# SPDX-License-Identifier: Unlicense
"""
`adafruit_pyportal.wifi`
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
import board
import busio
from digitalio import DigitalInOut
import neopixel
from adafruit_esp32spi import adafruit_esp32spi, adafruit_esp32spi_wifimanager
import adafruit_esp32spi.adafruit_esp32spi_socket as socket
import adafruit_requests as requests

__version__ = "5.1.3"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_PyPortal.git"


class WiFi:
    """Class representing the ESP.

    :param status_neopixel: The pin for the status NeoPixel. Use ``board.NEOPIXEL`` for the on-board
                            NeoPixel. Defaults to ``None``, not the status LED
    :param esp: A passed ESP32 object, Can be used in cases where the ESP32 chip needs to be used
                             before calling the pyportal class. Defaults to ``None``.
    :param busio.SPI external_spi: A previously declared spi object. Defaults to ``None``.

    """

    def __init__(self, *, status_neopixel=None, esp=None, external_spi=None):

        if status_neopixel:
            self.neopix = neopixel.NeoPixel(status_neopixel, 1, brightness=0.2)
        else:
            self.neopix = None
        self.neo_status(0)
        self.requests = None

        if external_spi:  # If SPI Object Passed
            spi = external_spi
        else:  # Else: Make ESP32 connection
            spi = busio.SPI(board.SCK, board.MOSI, board.MISO)

        if esp:  # If there was a passed ESP Object
            self.esp = esp
        else:
            esp32_ready = DigitalInOut(board.ESP_BUSY)
            esp32_gpio0 = DigitalInOut(board.ESP_GPIO0)
            esp32_reset = DigitalInOut(board.ESP_RESET)
            esp32_cs = DigitalInOut(board.ESP_CS)

            self.esp = adafruit_esp32spi.ESP_SPIcontrol(
                spi, esp32_cs, esp32_ready, esp32_reset, esp32_gpio0
            )

        requests.set_socket(socket, self.esp)
        self._manager = None

        gc.collect()

    def connect(self, ssid, password):
        """
        Connect to WiFi using the settings found in secrets.py
        """
        self.esp.connect({"ssid": ssid, "password": password})
        self.requests = requests

    def neo_status(self, value):
        """The status NeoPixel.

        :param value: The color to change the NeoPixel.

        """
        if self.neopix:
            self.neopix.fill(value)

    def manager(self, secrets):
        """Initialize the WiFi Manager if it hasn't been cached and return it"""
        if self._manager is None:
            self._manager = adafruit_esp32spi_wifimanager.ESPSPI_WiFiManager(
                self.esp, secrets, None
            )
        return self._manager

    @property
    def is_connected(self):
        """Return whether we are connected."""
        return self.esp.is_connected

    @property
    def enabled(self):
        """Not currently disablable on the ESP32 Coprocessor"""
        return True
