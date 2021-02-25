# SPDX-FileCopyrightText: 2020 Bryan Siepert, written for Adafruit Industries
# SPDX-License-Identifier: MIT
"""
`adafruit_bno08x_rvc`
================================================================================

A simple helper library for using the UART-RVC mode of the BNO08x IMUs

* Author(s): Bryan Siepert

Implementation Notes
--------------------

**Hardware:**

* `Adafruit BNO08x Breakout <https:www.adafruit.com/products/4754>`_

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://github.com/adafruit/circuitpython/releases

"""
import time
from struct import unpack_from

__version__ = "1.0.2"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_BNO08x_RVC.git"


class RVCReadTimeoutError(Exception):
    """Raised if a UART-RVC message cannot be read before the given timeout"""


class BNO08x_RVC:
    """A simple class for reading heading from the BNO08x IMUs using the UART-RVC mode"""

    def __init__(self, uart, timeout=1.0):
        self._uart = uart
        self._debug = True
        self._read_timeout = timeout

    @staticmethod
    def _parse_frame(frame):
        heading_frame = unpack_from("<BhhhhhhBBBB", frame)
        (
            _index,
            yaw,
            pitch,
            roll,
            x_accel,
            y_accel,
            z_accel,
            _res1,
            _res2,
            _res3,
            _checksum,
        ) = heading_frame
        checksum_calc = sum(frame[0:16]) % 256
        if checksum_calc != _checksum:
            return None
        yaw *= 0.01
        pitch *= 0.01
        roll *= 0.01
        x_accel *= 0.0098067
        y_accel *= 0.0098067
        z_accel *= 0.0098067
        return (yaw, pitch, roll, x_accel, y_accel, z_accel)

    @property
    def heading(self):
        """The current heading made up of

        * Yaw
        * Pitch
        * Roll
        * X-Axis Acceleration
        * Y-Axis Acceleration
        * Z-Axis Acceleration

        """
        # try to read initial packet start byte
        data = None
        start_time = time.monotonic()
        while time.monotonic() - start_time < self._read_timeout:
            data = self._uart.read(2)
            # print("data", data)
            if data[0] == 0xAA and data[1] == 0xAA:
                msg = self._uart.read(17)
                heading = self._parse_frame(msg)
                if heading is None:
                    continue
                return heading
        raise RVCReadTimeoutError("Unable to read RVC heading message")
