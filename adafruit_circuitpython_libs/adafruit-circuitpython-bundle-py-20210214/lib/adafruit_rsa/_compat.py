# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: 2011 Sybren A. Stüvel <sybren@stuvel.eu>
#
# SPDX-License-Identifier: Apache-2.0

"""Python compatibility wrappers."""

import sys
from struct import pack

__version__ = "1.2.2"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_RSA.git"

MAX_INT = sys.maxsize
MAX_INT64 = (1 << 63) - 1
MAX_INT32 = (1 << 31) - 1
MAX_INT16 = (1 << 15) - 1

# Determine the word size of the processor.
if MAX_INT == MAX_INT64:
    # 64-bit processor.
    MACHINE_WORD_SIZE = 64
elif MAX_INT == MAX_INT32:
    # 32-bit processor.
    MACHINE_WORD_SIZE = 32
else:
    # Else we just assume 64-bit processor keeping up with modern times.
    MACHINE_WORD_SIZE = 64


INTEGER_TYPES = (int,)


def write_to_stdout(data):
    """Writes bytes to stdout

    :type data: bytes
    """
    # On Py3 we must use the buffer interface to write bytes.
    sys.stdout.buffer.write(data)


def is_bytes(obj):
    """
    Determines whether the given value is a byte string.

    :param obj:
        The value to test.
    :returns:
        ``True`` if ``value`` is a byte string; ``False`` otherwise.
    """
    return isinstance(obj, bytes)


def is_integer(obj):
    """
    Determines whether the given value is an integer.

    :param obj:
        The value to test.
    :returns:
        ``True`` if ``value`` is an integer; ``False`` otherwise.
    """
    return isinstance(obj, INTEGER_TYPES)


def byte(num):
    """
    Converts a number between 0 and 255 (both inclusive) to a base-256 (byte)
    representation.

    Use it as a replacement for ``chr`` where you are expecting a byte
    because this will work on all current versions of Python::

    :param num:
        An unsigned integer between 0 and 255 (both inclusive).
    :returns:
        A single byte.
    """
    return pack("B", num)


def xor_bytes(bytes_1, bytes_2):
    """
    Returns the bitwise XOR result between two bytes objects, bytes_1 ^ bytes_2.

    Bitwise XOR operation is commutative, so order of parameters doesn't
    generate different results. If parameters have different length, extra
    length of the largest one is ignored.

    :param bytes_1:
        First bytes object.
    :param bytes_2:
        Second bytes object.
    :returns:
        Bytes object, result of XOR operation.
    """
    return bytes(x ^ y for x, y in zip(bytes_1, bytes_2))


def get_word_alignment(num, force_arch=64, _machine_word_size=MACHINE_WORD_SIZE):
    """
    Returns alignment details for the given number based on the platform
    Python is running on.

    :param num:
        Unsigned integral number.
    :param force_arch:
        If you don't want to use 64-bit unsigned chunks, set this to
        anything other than 64. 32-bit chunks will be preferred then.
        Default 64 will be used when on a 64-bit machine.
    :param _machine_word_size:
        (Internal) The machine word size used for alignment.
    :returns:
        4-tuple::

            (word_bits, word_bytes,
             max_uint, packing_format_type)
    """
    max_uint64 = 0xFFFFFFFFFFFFFFFF
    max_uint32 = 0xFFFFFFFF
    max_uint16 = 0xFFFF
    max_uint8 = 0xFF

    if force_arch == 64 and _machine_word_size >= 64 and num > max_uint32:
        # 64-bit unsigned integer.
        return 64, 8, max_uint64, "Q"
    if num > max_uint16:
        # 32-bit unsigned integer
        return 32, 4, max_uint32, "L"
    if num > max_uint8:
        # 16-bit unsigned integer.
        return 16, 2, max_uint16, "H"
    # 8-bit unsigned integer.
    return 8, 1, max_uint8, "B"
