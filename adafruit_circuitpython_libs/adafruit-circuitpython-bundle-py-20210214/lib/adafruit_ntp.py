# SPDX-FileCopyrightText: 2019 Brent Rubell for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_ntp`
================================================================================

Network Time Protocol (NTP) helper for CircuitPython

 * Author(s): Brent Rubell

Implementation Notes
--------------------
**Hardware:**
**Software and Dependencies:**

 * Adafruit CircuitPython firmware for the supported boards:
   https://github.com/adafruit/circuitpython/releases

"""
import time
import rtc

__version__ = "2.2.2"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_NTP.git"


class NTP:
    """Network Time Protocol (NTP) helper module for CircuitPython.
    This module does not handle daylight savings or local time.

    :param adafruit_esp32spi esp: ESP32SPI object.
    :param bool debug: Set to True to output set_time() failures to console
    """

    def __init__(self, esp, debug=False):
        # Verify ESP32SPI module
        if "ESP_SPIcontrol" in str(type(esp)):
            self._esp = esp
        else:
            raise TypeError("Provided object is not an ESP_SPIcontrol object.")
        self.valid_time = False
        self.debug = debug

    def set_time(self, tz_offset=0):
        """Fetches and sets the microcontroller's current time
        in seconds since since Jan 1, 1970.

        :param int tz_offset: The offset of the local timezone,
            in seconds west of UTC (negative in most of Western Europe,
            positive in the US, zero in the UK).
        """

        try:
            now = self._esp.get_time()
            now = time.localtime(now[0] + tz_offset)
            rtc.RTC().datetime = now
            self.valid_time = True
        except ValueError as error:
            if self.debug:
                print(str(error))
            return
