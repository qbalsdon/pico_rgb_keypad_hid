# SPDX-FileCopyrightText: Copyright (c) 2020 Bryan Siepert for Adafruit Industries
#
# SPDX-License-Identifier: MIT
"""

    Subclass of `adafruit_bno08x.BNO08X` to use UART

"""
import time
from struct import pack_into
from . import (
    BNO08X,
    BNO_CHANNEL_EXE,
    BNO_CHANNEL_SHTP_COMMAND,
    DATA_BUFFER_SIZE,
    Packet,
    PacketError,
)


class BNO08X_UART(BNO08X):
    """Library for the BNO08x IMUs from Hillcrest Laboratories

        :param uart: The UART devce the BNO08x is connected to.

    """

    def __init__(self, uart, reset=None, debug=False):
        self._uart = uart
        super().__init__(reset, debug)

    def _send_packet(self, channel, data):
        data_length = len(data)
        write_length = data_length + 4
        byte_buffer = bytearray(1)

        # request available size
        # pylint:disable=pointless-string-statement
        """
        self._uart.write(b'\x7e') # start byte
        time.sleep(0.001)
        self._uart.write(b'\x00') # SHTP byte
        time.sleep(0.001)
        self._uart.write(b'\x7e')
        avail = self._uart.read(5)
        if avail[0] != 0x7e and avail[1] != 0x01 and avail[4] != 0x7e:
            raise RuntimeError("Couldn't get available buffer size")
        """
        # pylint:enable=pointless-string-statement

        pack_into("<H", self._data_buffer, 0, write_length)
        self._data_buffer[2] = channel
        self._data_buffer[3] = self._sequence_number[channel]
        self._data_buffer[4 : 4 + data_length] = data
        self._uart.write(b"\x7e")  # start byte
        time.sleep(0.001)
        self._uart.write(b"\x01")  # SHTP byte
        time.sleep(0.001)
        for b in self._data_buffer[0:write_length]:
            byte_buffer[0] = b
            self._uart.write(byte_buffer)
            time.sleep(0.001)
        time.sleep(0.001)
        self._uart.write(b"\x7e")  # end byte

        # print("Sending", [hex(x) for x in self._data_buffer[0:write_length]])

        self._sequence_number[channel] = (self._sequence_number[channel] + 1) % 256
        return self._sequence_number[channel]

    def _read_into(self, buf, start=0, end=None):
        if end is None:
            end = len(buf)

        # print("Avail:", self._uart.in_waiting, "need", end-start)
        for idx in range(start, end):
            data = self._uart.read(1)
            b = data[0]
            if b == 0x7D:  # control escape
                data = self._uart.read(1)
                b = data[0]
                b ^= 0x20
            buf[idx] = b
        # print("UART Read buffer: ", [hex(i) for i in buf[start:end]])

    def _read_header(self):
        """Reads the first 4 bytes available as a header"""
        # try to read initial packet start byte
        data = None
        while True:
            data = self._uart.read(1)
            if not data:
                continue
            b = data[0]
            if b == 0x7E:
                break

        # read protocol id
        data = self._uart.read(1)
        if data and data[0] == 0x7E:  # second 0x7e
            data = self._uart.read(1)
        if not data or data[0] != 0x01:
            raise RuntimeError("Unhandled UART control SHTP protocol")
        # read header
        self._read_into(self._data_buffer, end=4)

        # print("SHTP Header:", [hex(x) for x in self._data_buffer[0:4]])

    def _read_packet(self):
        self._read_header()

        # print([hex(x) for x in self._data_buffer[0:4]])
        header = Packet.header_from_buffer(self._data_buffer)
        packet_byte_count = header.packet_byte_count
        channel_number = header.channel_number
        sequence_number = header.sequence_number

        self._sequence_number[channel_number] = sequence_number
        if packet_byte_count == 0:
            raise PacketError("No packet available")

        self._dbg(
            "channel %d has %d bytes available"
            % (channel_number, packet_byte_count - 4)
        )

        if packet_byte_count > DATA_BUFFER_SIZE:
            self._data_buffer = bytearray(packet_byte_count)

        # skip 4 header bytes since they've already been read
        self._read_into(self._data_buffer, start=4, end=packet_byte_count)

        # print("Packet: ", [hex(i) for i in self._data_buffer[0:packet_byte_count]])

        data = self._uart.read(1)
        b = data[0]
        if b != 0x7E:
            raise RuntimeError("Didn't find packet end")

        new_packet = Packet(self._data_buffer)
        if self._debug:
            print(new_packet)

        self._update_sequence_number(new_packet)

        return new_packet

    @property
    def _data_ready(self):
        return self._uart.in_waiting >= 4

    def soft_reset(self):
        """Reset the sensor to an initial unconfigured state"""
        print("Soft resetting...", end="")

        data = bytearray([0, 1])
        self._send_packet(BNO_CHANNEL_SHTP_COMMAND, data)
        time.sleep(0.5)

        # read the SHTP announce command packet response
        while True:
            packet = self._read_packet()
            if packet.channel_number == BNO_CHANNEL_SHTP_COMMAND:
                break

        data = bytearray([1])
        self._send_packet(BNO_CHANNEL_EXE, data)
        time.sleep(0.5)
        self._send_packet(BNO_CHANNEL_EXE, data)
        time.sleep(0.5)

        print("OK!")  # all is good!
