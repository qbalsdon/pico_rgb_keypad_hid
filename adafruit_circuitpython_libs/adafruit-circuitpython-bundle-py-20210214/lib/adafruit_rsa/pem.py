# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: 2011 Sybren A. Stüvel <sybren@stuvel.eu>
#
# SPDX-License-Identifier: Apache-2.0

"""Functions that load and write PEM-encoded files."""
from adafruit_binascii import a2b_base64, b2a_base64

# pylint: disable=redefined-builtin
from adafruit_rsa._compat import is_bytes

__version__ = "1.2.2"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_RSA.git"


def _markers(pem_marker):
    """
    Returns the start and end PEM markers, as bytes.
    """

    if not is_bytes(pem_marker):
        pem_marker = pem_marker.encode("ascii")

    return (
        b"-----BEGIN " + pem_marker + b"-----",
        b"-----END " + pem_marker + b"-----",
    )


def load_pem(contents, pem_marker):
    """Loads a PEM file.

    :param contents: the contents of the file to interpret
    :param pem_marker: the marker of the PEM content, such as 'RSA PRIVATE KEY'
        when your file has '-----BEGIN RSA PRIVATE KEY-----' and
        '-----END RSA PRIVATE KEY-----' markers.

    :return: the base64-decoded content between the start and end markers.

    @raise ValueError: when the content is invalid, for example when the start
        marker cannot be found.

    """

    # We want bytes, not text. If it's text, it can be converted to ASCII bytes.
    if not is_bytes(contents):
        contents = contents.encode("ascii")

    (pem_start, pem_end) = _markers(pem_marker)

    pem_lines = []
    in_pem_part = False

    for line in contents.split(b"\n"):
        line = line.strip()

        # Skip empty lines
        if not line:
            continue

        # Handle start marker
        if line == pem_start:
            if in_pem_part:
                raise ValueError('Seen start marker "%s" twice' % pem_start)

            in_pem_part = True
            continue

        # Skip stuff before first marker
        if not in_pem_part:
            continue

        # Handle end marker
        if in_pem_part and line == pem_end:
            in_pem_part = False
            break

        # Load fields
        if b":" in line:
            continue

        pem_lines.append(line)

    # Do some sanity checks
    if not pem_lines:
        raise ValueError('No PEM start marker "%s" found' % pem_start)

    if in_pem_part:
        raise ValueError('No PEM end marker "%s" found' % pem_end)

    # Base64-decode the contents
    pem = b"".join(pem_lines)
    return a2b_base64(pem)


def save_pem(contents, pem_marker):
    """Saves a PEM file.

    :param contents: the contents to encode in PEM format
    :param pem_marker: the marker of the PEM content, such as 'RSA PRIVATE KEY'
        when your file has '-----BEGIN RSA PRIVATE KEY-----' and
        '-----END RSA PRIVATE KEY-----' markers.

    :return: the base64-encoded content between the start and end markers, as bytes.

    """

    (pem_start, pem_end) = _markers(pem_marker)

    b64 = b2a_base64(contents).replace(b"\n", b"")
    pem_lines = [pem_start]

    for block_start in range(0, len(b64), 64):
        block = b64[block_start : block_start + 64]
        pem_lines.append(block)

    pem_lines.append(pem_end)
    pem_lines.append(b"")

    return b"\n".join(pem_lines)
