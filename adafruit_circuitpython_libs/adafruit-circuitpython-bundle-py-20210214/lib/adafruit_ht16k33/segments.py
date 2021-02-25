# SPDX-FileCopyrightText: Radomir Dopieralski 2016  for Adafruit Industries
# SPDX-FileCopyrightText: Tony DiCola 2016 for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
Segment Displays
=================
"""

from time import sleep
from adafruit_ht16k33.ht16k33 import HT16K33

__version__ = "4.1.3"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_HT16K33.git"

# fmt: off
CHARS = (
    0b00000000, 0b00000000, #
    0b01000000, 0b00000110, # !
    0b00000010, 0b00100000, # "
    0b00010010, 0b11001110, # #
    0b00010010, 0b11101101, # $
    0b00001100, 0b00100100, # %
    0b00100011, 0b01011101, # &
    0b00000100, 0b00000000, # '
    0b00100100, 0b00000000, # (
    0b00001001, 0b00000000, # )
    0b00111111, 0b11000000, # *
    0b00010010, 0b11000000, # +
    0b00001000, 0b00000000, # ,
    0b00000000, 0b11000000, # -
    0b00000000, 0b00000000, # .
    0b00001100, 0b00000000, # /
    0b00001100, 0b00111111, # 0
    0b00000000, 0b00000110, # 1
    0b00000000, 0b11011011, # 2
    0b00000000, 0b10001111, # 3
    0b00000000, 0b11100110, # 4
    0b00100000, 0b01101001, # 5
    0b00000000, 0b11111101, # 6
    0b00000000, 0b00000111, # 7
    0b00000000, 0b11111111, # 8
    0b00000000, 0b11101111, # 9
    0b00010010, 0b00000000, # :
    0b00001010, 0b00000000, # ;
    0b00100100, 0b01000000, # <
    0b00000000, 0b11001000, # =
    0b00001001, 0b10000000, # >
    0b01100000, 0b10100011, # ?
    0b00000010, 0b10111011, # @
    0b00000000, 0b11110111, # A
    0b00010010, 0b10001111, # B
    0b00000000, 0b00111001, # C
    0b00010010, 0b00001111, # D
    0b00000000, 0b11111001, # E
    0b00000000, 0b01110001, # F
    0b00000000, 0b10111101, # G
    0b00000000, 0b11110110, # H
    0b00010010, 0b00000000, # I
    0b00000000, 0b00011110, # J
    0b00100100, 0b01110000, # K
    0b00000000, 0b00111000, # L
    0b00000101, 0b00110110, # M
    0b00100001, 0b00110110, # N
    0b00000000, 0b00111111, # O
    0b00000000, 0b11110011, # P
    0b00100000, 0b00111111, # Q
    0b00100000, 0b11110011, # R
    0b00000000, 0b11101101, # S
    0b00010010, 0b00000001, # T
    0b00000000, 0b00111110, # U
    0b00001100, 0b00110000, # V
    0b00101000, 0b00110110, # W
    0b00101101, 0b00000000, # X
    0b00010101, 0b00000000, # Y
    0b00001100, 0b00001001, # Z
    0b00000000, 0b00111001, # [
    0b00100001, 0b00000000, # \
    0b00000000, 0b00001111, # ]
    0b00001100, 0b00000011, # ^
    0b00000000, 0b00001000, # _
    0b00000001, 0b00000000, # `
    0b00010000, 0b01011000, # a
    0b00100000, 0b01111000, # b
    0b00000000, 0b11011000, # c
    0b00001000, 0b10001110, # d
    0b00001000, 0b01011000, # e
    0b00000000, 0b01110001, # f
    0b00000100, 0b10001110, # g
    0b00010000, 0b01110000, # h
    0b00010000, 0b00000000, # i
    0b00000000, 0b00001110, # j
    0b00110110, 0b00000000, # k
    0b00000000, 0b00110000, # l
    0b00010000, 0b11010100, # m
    0b00010000, 0b01010000, # n
    0b00000000, 0b11011100, # o
    0b00000001, 0b01110000, # p
    0b00000100, 0b10000110, # q
    0b00000000, 0b01010000, # r
    0b00100000, 0b10001000, # s
    0b00000000, 0b01111000, # t
    0b00000000, 0b00011100, # u
    0b00100000, 0b00000100, # v
    0b00101000, 0b00010100, # w
    0b00101000, 0b11000000, # x
    0b00100000, 0b00001100, # y
    0b00001000, 0b01001000, # z
    0b00001001, 0b01001001, # {
    0b00010010, 0b00000000, # |
    0b00100100, 0b10001001, # }
    0b00000101, 0b00100000, # ~
    0b00111111, 0b11111111,
)
# fmt: on
NUMBERS = (
    0x3F,  # 0
    0x06,  # 1
    0x5B,  # 2
    0x4F,  # 3
    0x66,  # 4
    0x6D,  # 5
    0x7D,  # 6
    0x07,  # 7
    0x7F,  # 8
    0x6F,  # 9
    0x77,  # a
    0x7C,  # b
    0x39,  # C
    0x5E,  # d
    0x79,  # E
    0x71,  # F
    0x40,  # -
)


class Seg14x4(HT16K33):
    """Alpha-numeric, 14-segment display."""

    def print(self, value, decimal=0):
        """Print the value to the display."""
        if isinstance(value, (str)):
            self._text(value)
        elif isinstance(value, (int, float)):
            self._number(value, decimal)
        else:
            raise ValueError("Unsupported display value type: {}".format(type(value)))
        if self._auto_write:
            self.show()

    def print_hex(self, value):
        """Print the value as a hexidecimal string to the display."""
        if isinstance(value, int):
            self.print("{0:X}".format(value))
        else:
            self.print(value)

    def __setitem__(self, key, value):
        self._put(value, key)
        if self._auto_write:
            self.show()

    def scroll(self, count=1):
        """Scroll the display by specified number of places."""
        if count >= 0:
            offset = 0
        else:
            offset = 2
        for i in range(6):
            self._set_buffer(i + offset, self._get_buffer(i + 2 * count))

    def _put(self, char, index=0):
        """Put a character at the specified place."""
        if not 0 <= index <= 3:
            return
        if not 32 <= ord(char) <= 127:
            return
        if char == ".":
            self._set_buffer(
                index * 2 + 1, self._get_buffer(index * 2 + 1) | 0b01000000
            )
            return
        character = ord(char) * 2 - 64
        self._set_buffer(index * 2, CHARS[1 + character])
        self._set_buffer(index * 2 + 1, CHARS[character])

    def _push(self, char):
        """Scroll the display and add a character at the end."""
        if char != "." or self._get_buffer(7) & 0b01000000:
            self.scroll()
            self._put(" ", 3)
        self._put(char, 3)

    def _text(self, text):
        """Display the specified text."""
        for character in text:
            self._push(character)

    def _number(self, number, decimal=0):
        """
        Display a floating point or integer number on the Adafruit HT16K33 based displays

        Param: number - The floating point or integer number to be displayed, which must be
                in the range 0 (zero) to 9999 for integers and floating point or integer numbers
                and between 0.0 and 999.0 or 99.00 or 9.000 for floating point numbers.
        Param: decimal - The number of decimal places for a floating point number if decimal
                is greater than zero, or the input number is an integer if decimal is zero.

        Returns: The output text string to be displayed.
        """

        auto_write = self._auto_write
        self._auto_write = False
        stnum = str(number)
        dot = stnum.find(".")

        if (len(stnum) > 5) or ((len(stnum) > 4) and (dot < 0)):
            raise ValueError(
                "Input overflow - {0} is too large for the display!".format(number)
            )

        if dot < 0:
            # No decimal point (Integer)
            places = len(stnum)
        else:
            places = len(stnum[:dot])

        if places <= 0 < decimal:
            self.fill(False)
            places = 4

            if "." in stnum:
                places += 1

        # Set decimal places, if number of decimal places is specified (decimal > 0)
        if places > 0 < decimal < len(stnum[places:]) and dot > 0:
            txt = stnum[: dot + decimal + 1]
        elif places > 0:
            txt = stnum[:places]

        if len(txt) > 5:
            raise ValueError("Output string ('{0}') is too long!".format(txt))

        self._text(txt)
        self._auto_write = auto_write

        return txt

    def set_digit_raw(self, index, bitmask):
        """Set digit at position to raw bitmask value. Position should be a value
        of 0 to 3 with 0 being the left most character on the display.

        bitmask should be 2 bytes such as: 0xFFFF
        If can be passed as an integer, list, or tuple
        """
        if not isinstance(index, int) or not 0 <= index <= 3:
            raise ValueError("Index value must be an integer in the range: 0-3")

        if isinstance(bitmask, (tuple, list)):
            bitmask = ((bitmask[0] & 0xFF) << 8) | (bitmask[1] & 0xFF)

        # Use only the valid potion of bitmask
        bitmask &= 0xFFFF

        # Set the digit bitmask value at the appropriate position.
        self._set_buffer(index * 2, bitmask & 0xFF)
        self._set_buffer(index * 2 + 1, (bitmask >> 8) & 0xFF)

        if self._auto_write:
            self.show()

    def marquee(self, text, delay=0.25, loop=True):
        """
        Automatically scroll the text at the specified delay between characters

        :param str text: The text to display
        :param float delay: (optional) The delay in seconds to pause before scrolling
                            to the next character (default=0.25)
        :param bool loop: (optional) Whether to endlessly loop the text (default=True)

        """
        if isinstance(text, str):
            self.fill(False)
            if loop:
                while True:
                    self._scroll_marquee(text, delay)
            else:
                self._scroll_marquee(text, delay)

    def _scroll_marquee(self, text, delay):
        """Scroll through the text string once using the delay"""
        char_is_dot = False
        for character in text:
            self.print(character)
            # Add delay if character is not a dot or more than 2 in a row
            if character != "." or char_is_dot:
                sleep(delay)
            char_is_dot = character == "."
            self.show()


class Seg7x4(Seg14x4):
    """Numeric 7-segment display. It has the same methods as the alphanumeric display, but only
    supports displaying a limited set of characters."""

    POSITIONS = (0, 2, 6, 8)  #  The positions of characters.

    def __init__(self, i2c, address=0x70, auto_write=True):
        super().__init__(i2c, address, auto_write)
        # Use colon for controling two-dots indicator at the center (index 0)
        self._colon = Colon(self)

    def scroll(self, count=1):
        """Scroll the display by specified number of places."""
        if count >= 0:
            offset = 0
        else:
            offset = 1
        for i in range(3):
            self._set_buffer(
                self.POSITIONS[i + offset], self._get_buffer(self.POSITIONS[i + count])
            )

    def _push(self, char):
        """Scroll the display and add a character at the end."""
        if char in ":;":
            self._put(char)
        else:
            if char != "." or self._get_buffer(self.POSITIONS[3]) & 0b10000000:
                self.scroll()
                self._put(" ", 3)
            self._put(char, 3)

    def _put(self, char, index=0):
        """Put a character at the specified place."""
        if not 0 <= index <= 3:
            return
        char = char.lower()
        index = self.POSITIONS[index]
        if char == ".":
            self._set_buffer(index, self._get_buffer(index) | 0b10000000)
            return
        if char in "abcdef":
            character = ord(char) - 97 + 10
        elif char == "-":
            character = 16
        elif char in "0123456789":
            character = ord(char) - 48
        elif char == " ":
            self._set_buffer(index, 0x00)
            return
        elif char == ":":
            self._set_buffer(4, 0x02)
            return
        elif char == ";":
            self._set_buffer(4, 0x00)
            return
        else:
            return
        self._set_buffer(index, NUMBERS[character])

    def set_digit_raw(self, index, bitmask):
        """Set digit at position to raw bitmask value. Position should be a value
        of 0 to 3 with 0 being the left most digit on the display.
        """
        if not isinstance(index, int) or not 0 <= index <= 3:
            raise ValueError("Index value must be an integer in the range: 0-3")

        # Set the digit bitmask value at the appropriate position.
        self._set_buffer(self.POSITIONS[index], bitmask & 0xFF)

        if self._auto_write:
            self.show()

    @property
    def colon(self):
        """Simplified colon accessor"""
        return self._colon[0]

    @colon.setter
    def colon(self, turn_on):
        self._colon[0] = turn_on


class BigSeg7x4(Seg7x4):
    """Numeric 7-segment display. It has the same methods as the alphanumeric display, but only
    supports displaying a limited set of characters."""

    def __init__(self, i2c, address=0x70, auto_write=True):
        super().__init__(i2c, address, auto_write)
        # Use colon for controling two-dots indicator at the center (index 0)
        # or the two-dots indicators at the left (index 1)
        self.colon = Colon(self, 2)

    def _setindicator(self, index, value):
        """Set side LEDs (dots)
        Index is as follow :
        * 0 : two dots at the center
        * 1 : top-left dot
        * 2 : bottom-left dot
        * 3 : right dot (also ampm indicator)
        """
        bitmask = 1 << (index + 1)
        current = self._get_buffer(0x04)
        if value:
            self._set_buffer(0x04, current | bitmask)
        else:
            self._set_buffer(0x04, current & ~bitmask)
        if self._auto_write:
            self.show()

    def _getindicator(self, index):
        """Get side LEDs (dots)
        See setindicator() for indexes
        """
        bitmask = 1 << (index + 1)
        return self._get_buffer(0x04) & bitmask

    @property
    def top_left_dot(self):
        """The top-left dot indicator."""
        return bool(self._getindicator(1))

    @top_left_dot.setter
    def top_left_dot(self, value):
        self._setindicator(1, value)

    @property
    def bottom_left_dot(self):
        """The bottom-left dot indicator."""
        return bool(self._getindicator(2))

    @bottom_left_dot.setter
    def bottom_left_dot(self, value):
        self._setindicator(2, value)

    @property
    def ampm(self):
        """The AM/PM indicator."""
        return bool(self._getindicator(3))

    @ampm.setter
    def ampm(self, value):
        self._setindicator(3, value)


class Colon:
    """Helper class for controlling the colons. Not intended for direct use."""

    # pylint: disable=protected-access

    MASKS = (0x02, 0x0C)

    def __init__(self, disp, num_of_colons=1):
        self._disp = disp
        self._num_of_colons = num_of_colons

    def __setitem__(self, key, value):
        if key > self._num_of_colons - 1:
            raise ValueError("Trying to set a non-existent colon.")
        current = self._disp._get_buffer(0x04)
        if value:
            self._disp._set_buffer(0x04, current | self.MASKS[key])
        else:
            self._disp._set_buffer(0x04, current & ~self.MASKS[key])
        if self._disp.auto_write:
            self._disp.show()

    def __getitem__(self, key):
        if key > self._num_of_colons - 1:
            raise ValueError("Trying to access a non-existent colon.")
        return bool(self._disp._get_buffer(0x04) & self.MASKS[key])
