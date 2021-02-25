# SPDX-FileCopyrightText: 2019 Dan Halbert for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_bluefruit_connect.magnetometer_packet`
====================================================

Bluefruit Connect App Magnetometer data packet.

* Author(s): Dan Halbert for Adafruit Industries

"""

from ._xyz_packet import _XYZPacket


class MagnetometerPacket(_XYZPacket):
    """A packet of x, y, z float values from a magnetometer."""

    # Everything else is handled by _XYZPacket.
    _TYPE_HEADER = b"!M"


# Register this class with the superclass. This allows the user to import only what is needed.
MagnetometerPacket.register_packet_type()
