# SPDX-FileCopyrightText: 2019 Dan Halbert for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_bluefruit_connect.gyro_packet`
====================================================

Bluefruit Connect App Gyro data packet.

* Author(s): Dan Halbert for Adafruit Industries

"""

from ._xyz_packet import _XYZPacket


class GyroPacket(_XYZPacket):
    """A packet of x, y, z float values from a gyroscope."""

    # Everything else is handled by _XYZPacket.
    _TYPE_HEADER = b"!G"


# Register this class with the superclass. This allows the user to import only what is needed.
GyroPacket.register_packet_type()
