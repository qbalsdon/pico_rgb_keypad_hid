# SPDX-FileCopyrightText: 2017 Scott Shawcroft, written for Adafruit Industries
# SPDX-FileCopyrightText: Copyright (c) 2020 ladyada for Adafruit Industries
#
# SPDX-License-Identifier: MIT
"""
`adafruit_lc709203f`
================================================================================

Library for I2C LC709203F battery status and fuel gauge


* Author(s): ladyada

Implementation Notes
--------------------

**Hardware:**

 * Adafruit LC709023 Breakout: https://www.adafruit.com/product/4712

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://github.com/adafruit/circuitpython/releases

# * Adafruit's Bus Device library: https://github.com/adafruit/Adafruit_CircuitPython_BusDevice
# * Adafruit's Register library: https://github.com/adafruit/Adafruit_CircuitPython_Register
"""

from micropython import const
import adafruit_bus_device.i2c_device as i2c_device

__version__ = "2.0.0"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_LC709203F.git"

LC709203F_I2CADDR_DEFAULT = const(0x0B)
LC709203F_CMD_ICVERSION = const(0x11)
LC709203F_CMD_BATTPROF = const(0x12)
LC709203F_CMD_POWERMODE = const(0x15)
LC709203F_CMD_APA = const(0x0B)
LC709203F_CMD_INITRSOC = const(0x07)
LC709203F_CMD_CELLVOLTAGE = const(0x09)
LC709203F_CMD_CELLITE = const(0x0F)


class CV:
    """struct helper"""

    @classmethod
    def add_values(cls, value_tuples):
        """Add CV values to the class"""
        cls.string = {}
        cls.lsb = {}

        for value_tuple in value_tuples:
            name, value, string, lsb = value_tuple
            setattr(cls, name, value)
            cls.string[value] = string
            cls.lsb[value] = lsb

    @classmethod
    def is_valid(cls, value):
        """Validate that a given value is a member"""
        return value in cls.string


class PowerMode(CV):
    """Options for ``power_mode``"""

    pass  # pylint: disable=unnecessary-pass


PowerMode.add_values(
    (("OPERATE", 0x0001, "Operate", None), ("SLEEP", 0x0002, "Sleep", None),)
)


class PackSize(CV):
    """Options for ``pack_size``"""

    pass  # pylint: disable=unnecessary-pass


PackSize.add_values(
    (
        ("MAH100", 0x08, "100 mAh", 100),
        ("MAH200", 0x0B, "200 mAh", 200),
        ("MAH500", 0x10, "500 mAh", 500),
        ("MAH1000", 0x19, "1000 mAh", 1000),
        ("MAH2000", 0x2D, "2000 mAh", 2000),
        ("MAH3000", 0x36, "3000 mAh", 3000),
    )
)


class LC709203F:
    """Interface library for LC709203F battery monitoring and fuel gauge sensors"""

    def __init__(self, i2c_bus, address=LC709203F_I2CADDR_DEFAULT):
        self.i2c_device = i2c_device.I2CDevice(i2c_bus, address)
        self._buf = bytearray(10)
        self.power_mode = PowerMode.OPERATE  # pylint: disable=no-member
        self.pack_size = PackSize.MAH500  # pylint: disable=no-member
        self.battery_profile = 1
        self.init_RSOC()

    def init_RSOC(self):  # pylint: disable=invalid-name
        """ Initialize the state of charge calculator """
        self._write_word(LC709203F_CMD_INITRSOC, 0xAA55)

    @property
    def cell_voltage(self):
        """Returns floating point voltage"""
        return self._read_word(LC709203F_CMD_CELLVOLTAGE) / 1000

    @property
    def cell_percent(self):
        """Returns percentage of cell capacity"""
        return self._read_word(LC709203F_CMD_CELLITE) / 10

    @property
    def ic_version(self):
        """Returns read-only chip version"""
        return self._read_word(LC709203F_CMD_ICVERSION)

    @property
    def power_mode(self):
        """Returns current power mode (operating or sleeping)"""
        return self._read_word(LC709203F_CMD_POWERMODE)

    @power_mode.setter
    def power_mode(self, mode):
        if not PowerMode.is_valid(mode):
            raise AttributeError("power_mode must be a PowerMode")
        self._write_word(LC709203F_CMD_POWERMODE, mode)

    @property
    def battery_profile(self):
        """Returns current battery profile (0 or 1)"""
        return self._read_word(LC709203F_CMD_BATTPROF)

    @battery_profile.setter
    def battery_profile(self, mode):
        if not mode in (0, 1):
            raise AttributeError("battery_profile must be 0 or 1")
        self._write_word(LC709203F_CMD_BATTPROF, mode)

    @property
    def pack_size(self):
        """Returns current battery pack size"""
        return self._read_word(LC709203F_CMD_APA)

    @pack_size.setter
    def pack_size(self, size):
        if not PackSize.is_valid(size):
            raise AttributeError("pack_size must be a PackSize")
        self._write_word(LC709203F_CMD_APA, size)

    # pylint: disable=no-self-use
    def _generate_crc(self, data):
        """8-bit CRC algorithm for checking data"""
        crc = 0x00
        # calculates 8-Bit checksum with given polynomial
        for byte in data:
            crc ^= byte
            for _ in range(8):
                if crc & 0x80:
                    crc = (crc << 1) ^ 0x07
                else:
                    crc <<= 1
        return crc & 0xFF

    def _read_word(self, command):
        self._buf[0] = LC709203F_I2CADDR_DEFAULT * 2  # write byte
        self._buf[1] = command  # command / register
        self._buf[2] = self._buf[0] | 0x1  # read byte

        with self.i2c_device as i2c:
            i2c.write_then_readinto(
                self._buf, self._buf, out_start=1, out_end=2, in_start=3, in_end=7
            )
        crc8 = self._generate_crc(self._buf[0:5])
        if crc8 != self._buf[5]:
            raise RuntimeError("CRC failure on reading word")
        return (self._buf[4] << 8) | self._buf[3]

    def _write_word(self, command, data):
        self._buf[0] = LC709203F_I2CADDR_DEFAULT * 2  # write byte
        self._buf[1] = command  # command / register
        self._buf[2] = data & 0xFF
        self._buf[3] = (data >> 8) & 0xFF
        self._buf[4] = self._generate_crc(self._buf[0:4])

        with self.i2c_device as i2c:
            i2c.write(self._buf[1:5])
