# SPDX-FileCopyrightText: 2020 Jim Bennet for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""Computes a derived symmetric key from a secret and a message
:param str secret: The secret to use for the key
:param str msg: The message to use for the key
:returns: The derived symmetric key
:rtype: bytes
"""

from .base64 import b64decode, b64encode
from .hmac import new_hmac


def compute_derived_symmetric_key(secret: str, msg: str) -> bytes:
    """Computes a derived symmetric key from a secret and a message
    :param str secret: The secret to use for the key
    :param str msg: The message to use for the key
    :returns: The derived symmetric key
    :rtype: bytes
    """
    return b64encode(new_hmac(b64decode(secret), msg=msg.encode("utf8")).digest())
