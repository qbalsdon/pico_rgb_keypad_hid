# SPDX-FileCopyrightText: 2019 Melissa LeBlanc-Williams for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_featherwing.led_segments`
====================================================

Base Class for the AlphaNumeric FeatherWing and 7-Segment FeatherWing helpers_.

* Author(s): Melissa LeBlanc-Williams
"""

__version__ = "1.13.3"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_FeatherWing.git"

# pylint: disable-msg=unsubscriptable-object, unsupported-assignment-operation


class Segments:
    """Class representing an `Adafruit 14-segment AlphaNumeric FeatherWing
    <https://www.adafruit.com/product/3139>`_.

    Automatically uses the feather's I2C bus."""

    def __init__(self):
        self._segments = None

    def print(self, value):
        """
        Print a number or text to the display

        :param value: The text or number to display
        :type value: str or int or float

        """
        # Attempt to round off so we can still display the value
        if isinstance(value, float) and len(str(value)) > 5:
            value = round(value)

        self._segments.print(value)
        self._segments.show()

    def marquee(self, text, delay=0.25, loop=True):
        """
        Automatically scroll the text at the specified delay between characters

        :param str text: The text to display
        :param float delay: (optional) The delay in seconds to pause before scrolling
                            to the next character (default=0.25)
        :param bool loop: (optional) Whether to endlessly loop the text (default=True)

        """
        self._segments.marquee(text, delay, loop)

    def fill(self, fill):
        """Change all Segments on or off

        :param bool fill: True turns all segments on, False turns all segments off

        """
        if isinstance(fill, bool):
            self._segments.fill(1 if fill else 0)
            self._segments.show()
        else:
            raise ValueError("Must set to either True or False.")

    @property
    def blink_rate(self):
        """
        Blink Rate returns the current rate that the text blinks.
        0 = Off
        1-3 = Successively slower blink rates
        """
        return self._segments.blink_rate

    @blink_rate.setter
    def blink_rate(self, rate):
        self._segments.blink_rate = rate

    @property
    def brightness(self):
        """
        Brightness returns the current display brightness.
        0-15 = Dimmest to Brightest Setting
        """
        return round(self._segments.brightness * 15)

    @brightness.setter
    def brightness(self, brightness):
        if not 0 <= brightness <= 15:
            raise ValueError("Brightness must be a value between 0 and 15")
        self._segments.brightness = brightness / 15
