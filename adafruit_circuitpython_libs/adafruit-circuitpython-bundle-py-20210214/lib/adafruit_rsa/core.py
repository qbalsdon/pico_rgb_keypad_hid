# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: 2011 Sybren A. Stüvel <sybren@stuvel.eu>
#
# SPDX-License-Identifier: Apache-2.0

"""Core mathematical operations.

This is the actual core RSA implementation, which is only defined
mathematically on integers.
"""

# pylint: disable=invalid-name
from adafruit_rsa._compat import is_integer

__version__ = "1.2.2"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_RSA.git"


def fast_pow(x, e, m):
    """Performs fast modular exponentiation, saves RAM on small CPUs/micros.
    :param int x: Base
    :param int y: Exponent
    :param int e: Second exponent
    """
    X = x
    E = e
    Y = 1
    while E > 0:
        if E % 2 == 0:
            X = (X * X) % m
            E = E // 2
        else:
            Y = (X * Y) % m
            E = E - 1
    return Y


def assert_int(var, name):
    """Asserts provided variable is an integer."""
    if is_integer(var):
        return

    raise TypeError("%s should be an integer, not %s" % (name, var.__class__))


def encrypt_int(message, ekey, n):
    """Encrypts a message using encryption key 'ekey', working modulo n"""

    assert_int(message, "message")
    assert_int(ekey, "ekey")
    assert_int(n, "n")

    if message < 0:
        raise ValueError("Only non-negative numbers are supported")

    if message > n:
        raise OverflowError("The message %i is too long for n=%i" % (message, n))

    # return pow(message, ekey, n)
    # print('fast_pow({},{},{})'.format(message,ekey,n))
    return fast_pow(message, ekey, n)


def decrypt_int(cyphertext, dkey, n):
    """Decrypts a cypher text using the decryption key 'dkey', working modulo n"""

    assert_int(cyphertext, "cyphertext")
    assert_int(dkey, "dkey")
    assert_int(n, "n")

    message = fast_pow(cyphertext, dkey, n)
    return message
