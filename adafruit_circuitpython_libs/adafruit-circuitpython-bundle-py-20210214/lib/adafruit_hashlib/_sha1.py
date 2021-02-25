# SPDX-FileCopyrightText: 2013-2015 AJ Alt
# SPDX-FileCopyrightText: 2019 Brent Rubell for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`_sha1.py`
======================================================
SHA1 Hash Algorithm.

Pure-Python implementation by AJ Alt
https://github.com/ajalt/python-sha1/blob/master/sha1.py

Modified by Brent Rubell, 2019

* Author(s): AJ Alt, Brent Rubell
"""
import struct
from io import BytesIO
from micropython import const

# SHA Block size and message digest sizes, in bytes.
SHA_BLOCKSIZE = 64
SHA_DIGESTSIZE = 20

# initial hash value [FIPS 5.3.1]
K0 = const(0x5A827999)
K1 = const(0x6ED9EBA1)
K2 = const(0x8F1BBCDC)
K3 = const(0xCA62C1D6)


def _getbuf(data):
    """Converts data into ascii,
    returns bytes of data.
    :param str bytes bytearray data: Data to convert.

    """
    if isinstance(data, str):
        return data.encode("ascii")
    return bytes(data)


def _left_rotate(n, b):
    """Left rotate a 32-bit integer, n, by b bits.
    :param int n: 32-bit integer
    :param int b: Desired rotation amount, in bits.

    """
    return ((n << b) | (n >> (32 - b))) & 0xFFFFFFFF


# pylint: disable=invalid-name, too-many-arguments
def _hash_computation(chunk, h0, h1, h2, h3, h4):
    """Processes 64-bit chunk of data and returns new digest variables.
    Per FIPS [6.1.2]
    :param bytes bytearray chunk: 64-bit bytearray
    :param list h_tuple: List of hash values for the chunk

    """
    assert len(chunk) == 64, "Chunk size should be 64-bits"

    w = [0] * 80

    # Break chunk into sixteen 4-byte big-endian words w[i]
    for i in range(16):
        w[i] = struct.unpack(b">I", chunk[i * 4 : i * 4 + 4])[0]

    # Extend the sixteen 4-byte words into eighty 4-byte words
    for i in range(16, 80):
        w[i] = _left_rotate(w[i - 3] ^ w[i - 8] ^ w[i - 14] ^ w[i - 16], 1)

    # Init. hash values for chunk
    a = h0
    b = h1
    c = h2
    d = h3
    e = h4

    for i in range(80):
        if 0 <= i <= 19:
            # Use alternative 1 for f from FIPS PB 180-1 to avoid bitwise not
            f = d ^ (b & (c ^ d))
            k = K0
        elif 20 <= i <= 39:
            f = b ^ c ^ d
            k = K1
        elif 40 <= i <= 59:
            f = (b & c) | (b & d) | (c & d)
            k = K2
        elif 60 <= i <= 79:
            f = b ^ c ^ d
            k = K3

        a, b, c, d, e = (
            (_left_rotate(a, 5) + f + e + k + w[i]) & 0xFFFFFFFF,
            a,
            _left_rotate(b, 30),
            c,
            d,
        )

    # Add to chunk's hash result so far
    h0 = (h0 + a) & 0xFFFFFFFF
    h1 = (h1 + b) & 0xFFFFFFFF
    h2 = (h2 + c) & 0xFFFFFFFF
    h3 = (h3 + d) & 0xFFFFFFFF
    h4 = (h4 + e) & 0xFFFFFFFF

    return h0, h1, h2, h3, h4


# pylint: disable=too-few-public-methods, invalid-name
class sha1:
    """SHA-1 Hash Object"""

    digest_size = SHA_DIGESTSIZE
    block_size = SHA_BLOCKSIZE
    name = "sha1"

    def __init__(self, data=None):
        """Construct a SHA-1 hash object.
        :param bytes data: Optional data to process

        """
        # Initial Digest Variables
        self._h = (0x67452301, 0xEFCDAB89, 0x98BADCFE, 0x10325476, 0xC3D2E1F0)

        # bytes object with 0 <= len < 64 used to store the end of the message
        # if the message length is not congruent to 64
        self._unprocessed = b""

        # Length in bytes of all data that has been processed so far
        self._msg_byte_len = 0

        if data:
            self.update(data)

    def _create_digest(self):
        """Returns finalized digest variables for the data processed so far."""
        # pre-processing
        message = self._unprocessed
        message_len = self._msg_byte_len + len(message)

        # add trailing '1' bit (+ 0's padding) to string [FIPS 5.1.1]
        message += b"\x80"

        # append 0 <= k < 512 bits '0', so that the resulting message length (in bytes)
        # is congruent to 56 (mod 64)
        message += b"\x00" * ((56 - (message_len + 1) % 64) % 64)

        # append ml, the original message length, as a 64-bit big-endian integer.
        message_bit_length = message_len * 8
        message += struct.pack(b">Q", message_bit_length)

        # Process the final chunk
        h = _hash_computation(message[:64], *self._h)
        if len(message) == 64:
            return h
        return _hash_computation(message[64:], *h)

    def update(self, data):
        """Updates the hash object with bytes-like object, data.
        :param bytes data: bytearray or bytes object

        """
        # if we get a string, convert to a bytearray objects
        data = _getbuf(data)

        # Use BytesIO for stream-like reading
        if isinstance(data, (bytes, bytearray)):
            data = BytesIO(data)

        # Try to build a chunk out of the unprocessed data, if any
        chunk = self._unprocessed + data.read(64 - len(self._unprocessed))

        while len(chunk) == 64:
            self._h = _hash_computation(chunk, *self._h)
            # increase the length of the message by 64 bytes
            self._msg_byte_len += 64
            # read the next 64 bytes
            chunk = data.read(64)

        self._unprocessed = chunk
        return self

    def digest(self):
        """Returns the digest of the data passed to the update()
        method so far.

        """
        return b"".join(struct.pack(b">I", h) for h in self._create_digest())

    def hexdigest(self):
        """Like digest() except the digest is returned as a string object of
        double length, containing only hexadecimal digits.

        """
        return "".join(["%.2x" % i for i in self.digest()])
