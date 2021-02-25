# SPDX-FileCopyrightText: 2018 Arduino SA. All rights reserved.
# SPDX-FileCopyrightText: 2019 Brent Rubell for Adafruit Industries
#
# SPDX-License-Identifier: MIT

# Copyright (c) 2018 Arduino SA. All rights reserved.
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA

"""
`atecc_asn1`
================================================================================

ASN.1 Utilities for the Adafruit_ATECC Module.

* Author(s): Brent Rubell

Implementation Notes
--------------------

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://github.com/adafruit/circuitpython/releases
"""
import struct

# pylint: disable=invalid-name
def get_signature(signature, data):
    """Appends signature data to buffer."""
    # Signature algorithm
    data += b"\x30\x0a\x06\x08"
    # ECDSA with SHA256
    data += b"\x2a\x86\x48\xce\x3d\x04\x03\x02"
    r = signature[0]
    s = signature[32]
    r_len = 32
    s_len = 32

    while r == 0x00 and r_len > 1:
        r += 1
        r_len -= 1

    while s == 0x00 and s_len > 1:
        s += 1
        s_len -= 1

    if r & 0x80:
        r_len += 1

    if s & 0x80:
        s_len += 1

    data += b"\x03" + struct.pack("B", r_len + s_len + 7) + b"\x00"

    data += b"\x30" + struct.pack("B", r_len + s_len + 4)

    data += b"\x02" + struct.pack("B", r_len)

    if r & 0x80:
        data += b"\x00"
        r_len -= 1
    data += signature[0:r_len]

    if r & 0x80:
        r_len += 1

    data += b"\x02" + struct.pack("B", s_len)
    if s & 0x80:
        data += b"\x00"
        s_len -= 1

    data += signature[s_len:]

    if s & 0x80:
        s_len += 1

    return 21 + r_len + s_len


# pylint: disable=too-many-arguments
def get_issuer_or_subject(data, country, state_prov, locality, org, org_unit, common):
    """Appends issuer or subject, if they exist, to data."""
    if country:
        get_name(country, 0x06, data)
    if state_prov:
        get_name(state_prov, 0x08, data)
    if locality:
        get_name(locality, 0x07, data)
    if org:
        get_name(org, 0x0A, data)
    if org_unit:
        get_name(org_unit, 0x0B, data)
    if common:
        get_name(common, 0x03, data)


def get_name(name, obj_type, data):
    """Appends ASN.1 string in form: set -> seq -> objid -> string
    :param str name: String to append to buffer.
    :param int obj_type: Object identifier type.
    :param bytearray data: Buffer to write to.
    """
    # ASN.1 SET
    data += b"\x31" + struct.pack("B", len(name) + 9)
    # ASN.1 SEQUENCE
    data += b"\x30" + struct.pack("B", len(name) + 7)
    # ASN.1 OBJECT IDENTIFIER
    data += b"\x06\x03\x55\x04" + struct.pack("B", obj_type)

    # ASN.1 PRINTABLE STRING
    data += b"\x13" + struct.pack("B", len(name))
    data.extend(name)
    return len(name) + 11


def get_version(data):
    """Appends X.509 version to data."""
    #  If no extensions are present, but a UniqueIdentifier
    #  is present, the version SHOULD be 2 (value is 1) [4-1-2]
    data += b"\x02\x01\x00"


def get_sequence_header(length, data):
    """Appends sequence header to provided data."""
    data += b"\x30"
    if length > 255:
        data += b"\x82"
        data.append((length >> 8) & 0xFF)
    elif length > 127:
        data += b"\x81"
    length_byte = struct.pack("B", (length) & 0xFF)
    data += length_byte


def get_public_key(data, public_key):
    """Appends public key subject and object identifiers."""
    # Subject: Public Key
    data += b"\x30" + struct.pack("B", (0x59) & 0xFF) + b"\x30\x13"
    # Object identifier: EC Public Key
    data += b"\x06\x07\x2a\x86\x48\xce\x3d\x02\x01"
    # Object identifier: PRIME 256 v1
    data += b"\x06\x08\x2a\x86\x48\xce\x3d\x03\x01\x07\x03\x42\x00\x04"
    # Extend the buffer by the public key
    data += public_key


def get_signature_length(signature):
    """Return length of ECDSA signature.
    :param bytearray signature: Signed SHA256 hash.
    """
    r = signature[0]
    s = signature[32]
    r_len = 32
    s_len = 32

    while r == 0x00 and r_len > 1:
        r += 1
        r_len -= 1

    if r & 0x80:
        r_len += 1

    while s == 0x00 and s_len > 1:
        s += 1
        s_len -= 1

    if s & 0x80:
        s_len += 1
    return 21 + r_len + s_len


def get_sequence_header_length(seq_header_len):
    """Returns length of SEQUENCE header."""
    if seq_header_len > 255:
        return 4
    if seq_header_len > 127:
        return 3
    return 2


def issuer_or_subject_length(country, state_prov, city, org, org_unit, common):
    """Returns total length of provided certificate information."""
    tot_len = 0
    if country:
        tot_len += 11 + len(country)
    if state_prov:
        tot_len += 11 + len(state_prov)
    if city:
        tot_len += 11 + len(city)
    if org:
        tot_len += 11 + len(org)
    if org_unit:
        tot_len += 11 + len(org_unit)
    if common:
        tot_len += 11 + len(common)
    else:
        raise TypeError("Provided length must be > 0")
    return tot_len
