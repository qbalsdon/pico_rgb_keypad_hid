# SPDX-FileCopyrightText: 2019 Dan Halbert for Adafruit Industries
# SPDX-FileCopyrightText: 2019 Scott Shawcroft for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_ble_berrymed_pulse_oximeter.adafruit_ble_transparent_uart`
=============================================================================

This module provides Services used by MicroChip

"""

from adafruit_ble import Service
from adafruit_ble.uuid import VendorUUID
from adafruit_ble.characteristics.stream import StreamOut, StreamIn

__version__ = "2.0.5"
__repo__ = (
    "https://github.com/adafruit/Adafruit_CircuitPython_BLE_Contec_Pulse_Oximeter.git"
)


class TransparentUARTService(Service):
    """
    Provide UART-like functionality via MicroChip

    :param int timeout:  the timeout in seconds to wait
      for the first character and between subsequent characters.
    :param int buffer_size: buffer up to this many bytes.
      If more bytes are received, older bytes will be discarded.
    """

    # pylint: disable=no-member
    uuid = VendorUUID("49535343-FE7D-4AE5-8FA9-9FAFD205E455")
    _server_tx = StreamOut(
        uuid=VendorUUID("49535343-1E4D-4BD9-BA61-23C647249616"),
        timeout=1.0,
        buffer_size=64,
    )
    _server_rx = StreamIn(
        uuid=VendorUUID("49535343-8841-43F4-A8D4-ECBE34729BB3"),
        timeout=1.0,
        buffer_size=64,
    )

    def __init__(self, service=None):
        super().__init__(service=service)
        self.connectable = True
        if not service:
            self._rx = self._server_rx
            self._tx = self._server_tx
        else:
            # If we're a client then swap the characteristics we use.
            self._tx = self._server_rx
            self._rx = self._server_tx

    def read(self, nbytes=None):
        """
        Read characters. If ``nbytes`` is specified then read at most that many bytes.
        Otherwise, read everything that arrives until the connection times out.
        Providing the number of bytes expected is highly recommended because it will be faster.

        :return: Data read
        :rtype: bytes or None
        """
        return self._rx.read(nbytes)

    def readinto(self, buf, nbytes=None):
        """
        Read bytes into the ``buf``. If ``nbytes`` is specified then read at most
        that many bytes. Otherwise, read at most ``len(buf)`` bytes.

        :return: number of bytes read and stored into ``buf``
        :rtype: int or None (on a non-blocking error)
        """
        return self._rx.readinto(buf, nbytes)

    def readline(self):
        """
        Read a line, ending in a newline character.

        :return: the line read
        :rtype: bytes or None
        """
        return self._rx.readline()

    @property
    def in_waiting(self):
        """The number of bytes in the input buffer, available to be read."""
        return self._rx.in_waiting

    def reset_input_buffer(self):
        """Discard any unread characters in the input buffer."""
        self._rx.reset_input_buffer()

    def write(self, buf):
        """Write a buffer of bytes."""
        self._tx.write(buf)
