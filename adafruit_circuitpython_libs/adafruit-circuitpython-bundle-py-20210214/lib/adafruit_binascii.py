# SPDX-FileCopyrightText: 2014 Paul Sokolovsky for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_binascii`
================================================================================

Helpers for conversions between binary and ASCII


* Author(s): Paul Sokolovsky, Brent Rubell

Implementation Notes
--------------------

**Hardware:**

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://github.com/adafruit/circuitpython/releases

"""
try:
    from binascii import hexlify, unhexlify
except ImportError:
    pass

__version__ = "1.2.4"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_binascii.git"

# fmt: off
TABLE_A2B_B64 = (
    -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1,
    -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1,
    -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 62, -1, -1, -1, 63,
    52, 53, 54, 55, 56, 57, 58, 59, 60, 61, -1, -1, -1, -1, -1, -1,
    -1, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14,
    15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, -1, -1, -1, -1, -1,
    -1, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40,
    41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, -1, -1, -1, -1, -1,
    -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1,
    -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1,
    -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1,
    -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1,
    -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1,
    -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1,
    -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1,
    -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1,
)
# fmt: on

TABLE_B2A_B64 = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"


class Error(Exception):
    """Exception raised on errors. These are usually programming errors."""

    # pylint: disable=unnecessary-pass
    pass


if not "unhexlify" in globals():
    # pylint: disable=function-redefined
    def unhexlify(hexstr):
        """Return the binary data represented by hexstr.
        :param str hexstr: Hexadecimal string.

        """
        if len(hexstr) % 2 != 0:
            raise Error("Odd-length string")

        return bytes([int(hexstr[i : i + 2], 16) for i in range(0, len(hexstr), 2)])


if not "hexlify" in globals():
    # pylint: disable=function-redefined
    def hexlify(data):
        """Return the hexadecimal representation of the
        binary data. Every byte of data is converted into
        the corresponding 2-digit hex representation.
        The returned bytes object is therefore twice
        as long as the length of data.

        :param bytes data: Binary data, as bytes.

        """
        if not data:
            raise TypeError("Data provided is zero-length")
        data = "".join("%02x" % i for i in data)
        return bytes(data, "utf-8")


B2A_HEX = hexlify
A2B_HEX = unhexlify


def _transform(n):
    if n == -1:
        return "\xff"
    return chr(n)


TABLE_A2B_B64 = "".join(map(_transform, TABLE_A2B_B64))
assert len(TABLE_A2B_B64) == 256


def a2b_base64(b64_data):
    """Convert a block of base64 data back to binary and return the binary data.

    :param str b64_data: Base64 data.

    """
    res = []
    quad_pos = 0
    leftchar = 0
    leftbits = 0
    last_char_was_a_pad = False

    for char in b64_data:
        char = chr(char)
        if char == "=":
            if quad_pos > 2 or (quad_pos == 2 and last_char_was_a_pad):
                break  # stop on 'xxx=' or on 'xx=='
            last_char_was_a_pad = True
        else:
            n = ord(TABLE_A2B_B64[ord(char)])
            if n == 0xFF:
                continue  # ignore strange characters
            #
            # Shift it in on the low end, and see if there's
            # a byte ready for output.
            quad_pos = (quad_pos + 1) & 3
            leftchar = (leftchar << 6) | n
            leftbits += 6
            #
            if leftbits >= 8:
                leftbits -= 8
                res.append((leftchar >> leftbits).to_bytes(1, "big"))
                leftchar &= (1 << leftbits) - 1
            #
            last_char_was_a_pad = False
    else:
        if leftbits != 0:
            raise Exception("Incorrect padding")

    return b"".join(res)


def b2a_base64(bin_data):
    """Convert binary data to a line of ASCII characters in base64 coding.

    :param str bin_data: Binary data string, as bytes

    """
    newlength = (len(bin_data) + 2) // 3
    newlength = newlength * 4 + 1
    res = []

    leftchar = 0
    leftbits = 0
    for char in bin_data:
        # Shift into our buffer, and output any 6bits ready
        leftchar = (leftchar << 8) | char
        leftbits += 8
        res.append(TABLE_B2A_B64[(leftchar >> (leftbits - 6)) & 0x3F])
        leftbits -= 6
        if leftbits >= 6:
            res.append(TABLE_B2A_B64[(leftchar >> (leftbits - 6)) & 0x3F])
            leftbits -= 6
    #
    if leftbits == 2:
        res.append(TABLE_B2A_B64[(leftchar & 3) << 4])
        res.append("=")
        res.append("=")
    elif leftbits == 4:
        res.append(TABLE_B2A_B64[(leftchar & 0xF) << 2])
        res.append("=")
    res.append("\n")
    return bytes("".join(res), "ascii")
