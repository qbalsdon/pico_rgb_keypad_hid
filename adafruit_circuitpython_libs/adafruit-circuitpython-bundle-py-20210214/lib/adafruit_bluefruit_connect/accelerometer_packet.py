# SPDX-FileCopyrightText: 2019 Dan Halbert for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_bluefruit_connect.accelerometer_packet`
====================================================

Bluefruit Connect App Accelerometer data packet.

* Author(s): Dan Halbert for Adafruit Industries

"""

from ._xyz_packet import _XYZPacket


class AccelerometerPacket(_XYZPacket):
    """A packet of x, y, z float values from an accelerometer."""

    # Everything else is handled by _XYZPacket.
    _TYPE_HEADER = b"!A"


# Register this class with the superclass. This allows the user to import only what is needed.
AccelerometerPacket.register_packet_type()
