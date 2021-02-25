# SPDX-FileCopyrightText: 2019 Dan Halbert for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_bluefruit_connect.button_packet`
====================================================

Bluefruit Connect App Button data packet (button_name, pressed/released)


* Author(s): Dan Halbert for Adafruit Industries

"""

import struct

from .packet import Packet


class ButtonPacket(Packet):
    """A packet containing a button name and its state."""

    BUTTON_1 = "1"
    """Code for Button 1 on the Bluefruit LE Connect app Control Pad screen."""
    BUTTON_2 = "2"
    """Button 2."""
    BUTTON_3 = "3"
    """Button 3."""
    BUTTON_4 = "4"
    """Button 4."""
    # pylint: disable= invalid-name
    UP = "5"
    """Up Button."""
    DOWN = "6"
    """Down Button."""
    LEFT = "7"
    """Left Button."""
    RIGHT = "8"
    """Right Button."""

    _FMT_PARSE = "<xxssx"
    PACKET_LENGTH = struct.calcsize(_FMT_PARSE)
    # _FMT_CONSTRUCT doesn't include the trailing checksum byte.
    _FMT_CONSTRUCT = "<2sss"
    _TYPE_HEADER = b"!B"

    def __init__(self, button, pressed):
        """Construct a ButtonPacket from a button name and the button's state.

        :param str button: a single character denoting the button
        :param bool pressed: ``True`` if button is pressed; ``False`` if it is
                             released.
        """
        # This check will catch wrong length and also non-sequence args (like an int).
        try:
            assert len(button) == 1
        except Exception as err:
            raise ValueError("Button must be a single char or byte.") from err

        self._button = button
        self._pressed = pressed

    @classmethod
    def parse_private(cls, packet):
        """Construct a ButtonPacket from an incoming packet.
        Do not call this directly; call Packet.from_bytes() instead.
        pylint makes it difficult to call this method _parse(), hence the name.
        """
        button, pressed = struct.unpack(cls._FMT_PARSE, packet)
        if not pressed in b"01":
            raise ValueError("Bad button press/release value")
        return cls(chr(button[0]), pressed == b"1")

    def to_bytes(self):
        """Return the bytes needed to send this packet."""
        partial_packet = struct.pack(
            self._FMT_CONSTRUCT,
            self._TYPE_HEADER,
            self._button,
            b"1" if self._pressed else b"0",
        )
        return self.add_checksum(partial_packet)

    @property
    def button(self):
        """A single character string (not bytes) specifying the button that
        the user pressed or released."""
        return self._button

    @property
    def pressed(self):
        """``True`` if button is pressed, or ``False`` if it is released."""
        return self._pressed


# Register this class with the superclass. This allows the user to import only what is needed.
ButtonPacket.register_packet_type()
