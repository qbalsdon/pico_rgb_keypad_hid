# SPDX-FileCopyrightText: 2018 ladyada for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_tfmini`
====================================================

A CircuitPython/Python library for Benewake's TF mini distance sensor

* Author(s): ladyada

Implementation Notes
--------------------

**Hardware:**

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://github.com/adafruit/circuitpython/releases

"""

import time
import struct

__version__ = "1.2.4"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_TFmini.git"

_STARTCONFIG = b"\x42\x57\x02\x00\x00\x00\x01\x02"
_STARTREPLY = b"\x57\x02\x01\x00\x00\x01\x02"  # minus header 0x42
_CONFIGPARAM = b"\x42\x57\x02\x00"
_ENDCONFIG = b"\x42\x57\x02\x00\x00\x00\x00\x02"
_ENDREPLY = b"\x42\x57\x02\x01\x00\x00\x00\x02"

MODE_SHORT = 2
MODE_LONG = 7


class TFmini:
    """TF mini communication module, use with just RX or TX+RX for advanced
    command & control.
    :param uart: the pyseral or busio.uart compatible uart device
    :param timeout: how long we'll wait for valid data or response, in seconds. Default is 1
    """

    def __init__(self, uart, *, timeout=1):
        self._uart = uart
        self._uart.baudrate = 115200
        self.timeout = timeout
        self._strength = None
        self._mode = None

    @property
    def distance(self):
        """The most recent distance measurement in centimeters"""
        try:
            self._uart.reset_input_buffer()
        except AttributeError:
            # not implemented, we'll just keep going
            pass

        # listen for new packet
        stamp = time.monotonic()
        while time.monotonic() - stamp < self.timeout:
            # look for the header start
            x = self._uart.read(1)
            if not x or x[0] != 0x59:
                continue
            # get remaining packet
            data = self._uart.read(8)
            # check first byte is magicbyte
            frame, dist, self._strength, self._mode, _, checksum = struct.unpack(
                "<BHHBBB", data
            )
            # look for second 0x59 frame indicator
            if frame != 0x59:
                continue
            # calculate and check sum
            mysum = (sum(data[0:7]) + 0x59) & 0xFF
            if mysum != checksum:
                continue
            return dist
        raise RuntimeError("Timed out looking for valid data")

    @property
    def strength(self):
        """The signal validity, higher value means better measurement"""
        _ = self.distance  # trigger distance measurement
        return self._strength

    @property
    def mode(self):
        """The measurement mode can be MODE_SHORT (2) or MODE_LONG (7)"""
        _ = self.distance  # trigger distance measurement
        return self._mode

    @mode.setter
    def mode(self, newmode):
        if not newmode in (MODE_LONG, MODE_SHORT):
            raise ValueError("Invalid mode")
        self._set_config(_CONFIGPARAM + bytes([0, 0, newmode, 0x11]))

    def _set_config(self, command):
        """Manager for sending commands, put sensor into config mode, config,
        then exit configuration mode!"""
        self._uart.write(_STARTCONFIG)
        stamp = time.monotonic()
        while (time.monotonic() - stamp) < self.timeout:
            # look for the header start
            x = self._uart.read(1)
            if not x or x[0] != 0x42:
                continue
            echo = self._uart.read(len(_STARTREPLY))
            # print("start ", [hex(i) for i in echo])
            if echo != _STARTREPLY:
                raise RuntimeError("Did not receive config start echo")
            break

        # Finally, send the command
        self._uart.write(command)
        # print([hex(i) for i in command])
        echo = self._uart.read(len(command))
        cmdreply = bytearray(len(command))
        cmdreply[:] = command
        cmdreply[3] = 0x1
        # print("cmd ", [hex(i) for i in echo])
        if echo != cmdreply:
            raise RuntimeError("Did not receive config command echo")

        self._uart.write(_ENDCONFIG)
        echo = self._uart.read(len(_ENDREPLY))
        # print("end ", [hex(i) for i in echo])
        if echo != _ENDREPLY:
            raise RuntimeError("Did not receive config end echo")
