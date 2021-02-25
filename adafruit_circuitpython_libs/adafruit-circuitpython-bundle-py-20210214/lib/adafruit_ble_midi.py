# SPDX-FileCopyrightText: 2020 Scott Shawcroft for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_ble_midi`
================================================================================

BLE MIDI service for CircuitPython

"""

import time

import _bleio

from adafruit_ble.attributes import Attribute
from adafruit_ble.characteristics import Characteristic, ComplexCharacteristic
from adafruit_ble.uuid import VendorUUID
from adafruit_ble.services import Service

__version__ = "1.0.3"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_BLE_MIDI.git"


class _MidiCharacteristic(ComplexCharacteristic):
    """Endpoint for sending commands to a media player. The value read will list all available

    commands."""

    uuid = VendorUUID("7772E5DB-3868-4112-A1A9-F2669D106BF3")

    def __init__(self):
        super().__init__(
            properties=Characteristic.WRITE_NO_RESPONSE
            | Characteristic.READ
            | Characteristic.NOTIFY,
            read_perm=Attribute.ENCRYPT_NO_MITM,
            write_perm=Attribute.ENCRYPT_NO_MITM,
            max_length=512,
            fixed_length=False,
        )

    def bind(self, service):
        """Binds the characteristic to the given Service."""
        bound_characteristic = super().bind(service)
        return _bleio.PacketBuffer(bound_characteristic, buffer_size=4)


class MIDIService(Service):
    """BLE MIDI service. It acts just like a USB MIDI PortIn and PortOut and can be used as a drop
    in replacement.

    BLE MIDI's protocol includes timestamps for MIDI messages. This class automatically adds them
    to MIDI data written out and strips them from MIDI data read in."""

    uuid = VendorUUID("03B80E5A-EDE8-4B33-A751-6CE34EC4C700")
    _raw = _MidiCharacteristic()
    # _raw gets shadowed for each MIDIService instance by a PacketBuffer. PyLint doesn't know this
    # so it complains about missing members.
    # pylint: disable=no-member

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Defer creating _in_buffer until we're definitely connected.
        self._in_buffer = None
        self._out_buffer = None
        shared_buffer = memoryview(bytearray(4))
        self._buffers = [
            None,
            shared_buffer[:1],
            shared_buffer[:2],
            shared_buffer[:3],
            shared_buffer[:4],
        ]
        self._header = bytearray(1)
        self._in_sysex = False
        self._message_target_length = None
        self._message_length = 0
        self._pending_realtime = None
        self._in_length = 0
        self._in_index = 1
        self._last_data = True

    def readinto(self, buf, length):
        """Reads up to ``length`` bytes into ``buf`` starting at index 0.

        Returns the number of bytes written into ``buf``."""
        if self._in_buffer is None:
            self._in_buffer = bytearray(self._raw.packet_size)
        i = 0
        while i < length:
            if self._in_index < self._in_length:
                byte = self._in_buffer[self._in_index]
                if self._last_data and byte & 0x80 != 0:
                    # Maybe manage timing here. Not done now because we're likely slower than we
                    # need to be already.
                    # low_ms = byte & 0x7f
                    # print("low", low_ms)
                    self._in_index += 1
                    self._last_data = False
                    continue
                self._in_index += 1
                self._last_data = True
                buf[i] = byte
                i += 1
            else:
                self._in_length = self._raw.readinto(self._in_buffer)
                if self._in_length == 0:
                    break
                # high_ms = self._in_buffer[0] & 0x3f
                # print("high", high_ms)
                self._in_index = 1
                self._last_data = True

        return i

    def read(self, length):
        """Reads up to ``length`` bytes and returns them."""
        result = bytearray(length)
        i = self.readinto(result, length)
        return result[:i]

    def write(self, buf, length):
        """Writes ``length`` bytes out."""
        # pylint: disable=too-many-branches
        timestamp_ms = time.monotonic_ns() // 1000000
        self._header[0] = (timestamp_ms >> 7 & 0x3F) | 0x80
        i = 0
        while i < length:
            data = buf[i]
            command = data & 0x80 != 0
            if self._in_sysex:
                if command:  # End of sysex or real time
                    b = self._buffers[2]
                    b[0] = 0x80 | (timestamp_ms & 0x7F)
                    b[1] = 0xF7
                    self._raw.write(b, header=self._header)
                    self._in_sysex = data == 0xF7
                else:
                    b = self._buffers[1]
                    b[0] = data
                    self._raw.write(b, header=self._header)
            elif command:
                self._in_sysex = data == 0xF0
                b = self._buffers[2]
                b[0] = 0x80 | (timestamp_ms & 0x7F)
                b[1] = data
                if (
                    0xF6 <= data <= 0xFF or self._in_sysex
                ):  # Real time, command only or start sysex
                    if self._message_target_length:
                        self._pending_realtime = b
                    else:
                        self._raw.write(b, header=self._header)
                else:
                    if (
                        0x80 <= data <= 0xBF or 0xE0 <= data <= 0xEF or data == 0xF2
                    ):  # Two following bytes
                        self._message_target_length = 4
                    else:
                        self._message_target_length = 3
                    b = self._buffers[self._message_target_length]
                    # All of the buffers share memory so the timestamp and data have already been
                    # set.
                    self._message_length = 2
                    self._out_buffer = b
            else:
                self._out_buffer[self._message_length] = data
                self._message_length += 1
                if self._message_target_length == self._message_length:
                    self._raw.write(self._out_buffer, header=self._header)
                    if self._pending_realtime:
                        self._raw.write(self._pending_realtime, header=self._header)
                        self._pending_realtime = None
                    self._message_target_length = None
            i += 1
