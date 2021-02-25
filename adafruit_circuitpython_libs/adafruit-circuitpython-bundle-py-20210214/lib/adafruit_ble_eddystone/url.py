# The MIT License (MIT)
#
# Copyright (c) 2020 Scott Shawcroft for Adafruit Industries LLC
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
"""
`adafruit_ble_eddystone.url`
================================================================================

Eddystone URL advertisement. Documented by Google here:
https://github.com/google/eddystone/tree/master/eddystone-url

"""

from . import EddystoneAdvertisement, EddystoneFrameStruct, EddystoneFrameBytes

__version__ = "1.0.2"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_BLE_Eddystone.git"

# These prefixes are replaced with a single one-byte scheme number.
_URL_SCHEMES = (b"http://www.", b"https://www.", b"http://", b"https://")

# These common domains are replaced with a single non-printing byte.
# Byte value is 0-6 for these with a '/' suffix.
# Byte value is 7-13 for these without the '/' suffix.
_SUBSTITUTIONS = (
    b".com",
    b".org",
    b".edu",
    b".net",
    b".info",
    b".biz",
    b".gov",
)


class _EncodedEddystoneUrl(EddystoneFrameBytes):
    """Packs and unpacks an encoded url"""

    def __get__(self, obj, cls):
        if obj is None:
            return self
        short_url = bytes(super().__get__(obj, cls))

        if short_url[0] < len(_URL_SCHEMES):
            short_url = _URL_SCHEMES[short_url[0]] + short_url[1:]

        for code, subst in enumerate(_SUBSTITUTIONS):
            code = bytes(chr(code), "ascii")
            short_url = short_url.replace(code, subst + b"/")
        for code, subst in enumerate(_SUBSTITUTIONS, 7):
            code = bytes(chr(code), "ascii")
            short_url = short_url.replace(code, subst)

        return str(short_url, "ascii")

    def __set__(self, obj, url):
        short_url = None
        url = bytes(url, "ascii")
        for idx, prefix in enumerate(_URL_SCHEMES):
            if url.startswith(prefix):
                short_url = url[len(prefix) :]
                short_url = bytes(chr(idx), "ascii") + short_url
                break
        if not short_url:
            raise ValueError("url does not start with one of: ", _URL_SCHEMES)
        for code, subst in enumerate(_SUBSTITUTIONS):
            code = bytes(chr(code), "ascii")
            short_url = short_url.replace(subst + b"/", code)
        for code, subst in enumerate(_SUBSTITUTIONS, 7):
            code = bytes(chr(code), "ascii")
            short_url = short_url.replace(subst, code)

        super().__set__(obj, short_url)


class EddystoneURL(EddystoneAdvertisement):
    """Eddystone URL broadcast.

    :param str url: Target url
    :param int tx_power: TX power in dBm"""

    match_prefixes = (b"\x03\xaa\xfe", b"\x16\xaa\xfe\x10")
    frame_type = b"\x10"
    tx_power = EddystoneFrameStruct("<B", offset=0)
    """TX power in dBm"""

    url = _EncodedEddystoneUrl(offset=1)
    """Target url"""

    def __init__(self, url=None, *, tx_power=0):
        super().__init__(minimum_size=1)
        self.tx_power = tx_power
        self.url = url
