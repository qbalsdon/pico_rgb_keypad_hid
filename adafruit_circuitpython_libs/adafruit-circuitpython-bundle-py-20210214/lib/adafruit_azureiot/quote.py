# SPDX-FileCopyrightText: 2020 Jim Bennet for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`quote`
================================================================================

The quote function %-escapes all characters that are neither in the
unreserved chars ("always safe") nor the additional chars set via the
safe arg.

"""
_ALWAYS_SAFE = frozenset(
    b"ABCDEFGHIJKLMNOPQRSTUVWXYZ" b"abcdefghijklmnopqrstuvwxyz" b"0123456789" b"_.-~"
)
_ALWAYS_SAFE_BYTES = bytes(_ALWAYS_SAFE)
SAFE_QUOTERS = {}


def quote(bytes_val: bytes, safe="/"):
    """The quote function %-escapes all characters that are neither in the
    unreserved chars ("always safe") nor the additional chars set via the
    safe arg.
    """
    if not isinstance(bytes_val, (bytes, bytearray)):
        raise TypeError("quote_from_bytes() expected bytes")
    if not bytes_val:
        return ""
    if isinstance(safe, str):
        # Normalize 'safe' by converting to bytes and removing non-ASCII chars
        safe = safe.encode("ascii", "ignore")
    else:
        safe = bytes([char for char in safe if char < 128])
    if not bytes_val.rstrip(_ALWAYS_SAFE_BYTES + safe):
        return bytes_val.decode()
    try:
        quoter = SAFE_QUOTERS[safe]
    except KeyError:
        SAFE_QUOTERS[safe] = quoter = Quoter(safe).__getitem__
    return "".join([quoter(char) for char in bytes_val])


# pylint: disable=C0103
class defaultdict:
    """
    Default Dict Implementation.

    Defaultdcit that returns the key if the key is not found in dictionnary (see
    unswap in karma-lib):
    >>> d = defaultdict(default=lambda key: key)
    >>> d['foo'] = 'bar'
    >>> d['foo']
    'bar'
    >>> d['baz']
    'baz'
    DefaultDict that returns an empty string if the key is not found (see
    prefix in karma-lib for typical usage):
    >>> d = defaultdict(default=lambda key: '')
    >>> d['foo'] = 'bar'
    >>> d['foo']
    'bar'
    >>> d['baz']
    ''
    Representation of a default dict:
    >>> defaultdict([('foo', 'bar')])
    defaultdict(None, {'foo': 'bar'})
    """

    @staticmethod
    # pylint: disable=W0613
    def __new__(cls, default_factory=None, **kwargs):
        self = super(defaultdict, cls).__new__(cls)
        # pylint: disable=C0103
        self.d = {}
        return self

    def __init__(self, default_factory=None, **kwargs):
        self.d = kwargs
        self.default_factory = default_factory

    def __getitem__(self, key):
        try:
            return self.d[key]
        except KeyError:
            val = self.__missing__(key)
            self.d[key] = val
            return val

    def __setitem__(self, key, val):
        self.d[key] = val

    def __delitem__(self, key):
        del self.d[key]

    def __contains__(self, key):
        return key in self.d

    def __missing__(self, key):
        if self.default_factory is None:
            raise KeyError(key)
        return self.default_factory()


class Quoter(defaultdict):
    """A mapping from bytes (in range(0,256)) to strings.

    String values are percent-encoded byte values, unless the key < 128, and
    in the "safe" set (either the specified safe set, or default set).
    """

    # Keeps a cache internally, using defaultdict, for efficiency (lookups
    # of cached keys don't call Python code at all).
    def __init__(self, safe):
        """safe: bytes object."""
        super().__init__()
        self.safe = _ALWAYS_SAFE.union(safe)

    def __missing__(self, b):
        # Handle a cache miss. Store quoted string in cache and return.
        res = chr(b) if b in self.safe else "%{:02X}".format(b)
        self[b] = res
        return res
