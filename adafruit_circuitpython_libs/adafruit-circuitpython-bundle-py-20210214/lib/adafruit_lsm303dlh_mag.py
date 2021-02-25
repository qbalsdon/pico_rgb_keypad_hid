# SPDX-FileCopyrightText: 2019 Bryan Siepert for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_lsm303dlh_mag`
====================================================


CircuitPython driver for the LSM303DLH's magnetometer.

* Author(s): Dave Astels, Bryan Siepert

Implementation Notes
--------------------

**Hardware:**

* Adafruit `Triple-axis Accelerometer+Magnetometer (Compass) Board - LSM303
  <https://www.adafruit.com/product/1120>`_ (Product ID: 1120)
* Adafruit `FLORA Accelerometer/Compass Sensor - LSM303 - v1.0
  <https://www.adafruit.com/product/1247>`_ (Product ID: 1247)

**Software and Dependencies:**

* Adafruit CircuitPython firmware:
  https://circuitpython.org/downloads
* Adafruit's Bus Device library:
  https://github.com/adafruit/Adafruit_CircuitPython_BusDevice
"""

try:
    import struct
except ImportError:
    import ustruct as struct
from micropython import const
from adafruit_bus_device.i2c_device import I2CDevice

__version__ = "1.1.6"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_LSM303DLH_Mag.git"

_ADDRESS_MAG = const(0x1E)  # (0x3C >> 1)       // 0011110x
_ID = const(0xD4)  # (0b11010100)

# Magnetometer registers
_REG_MAG_CRA_REG_M = const(0x00)
_REG_MAG_CRB_REG_M = const(0x01)
_REG_MAG_MR_REG_M = const(0x02)
_REG_MAG_OUT_X_H_M = const(0x03)
_REG_MAG_OUT_X_L_M = const(0x04)
_REG_MAG_OUT_Z_H_M = const(0x05)
_REG_MAG_OUT_Z_L_M = const(0x06)
_REG_MAG_OUT_Y_H_M = const(0x07)
_REG_MAG_OUT_Y_L_M = const(0x08)
_REG_MAG_SR_REG_M = const(0x09)
_REG_MAG_IRA_REG_M = const(0x0A)
_REG_MAG_IRB_REG_M = const(0x0B)
_REG_MAG_IRC_REG_M = const(0x0C)

_REG_MAG_TEMP_OUT_H_M = const(0x31)
_REG_MAG_TEMP_OUT_L_M = const(0x32)


MAG_DEVICE_ID = 0b01000000
# Magnetometer gains
MAGGAIN_1_3 = const(0x20)  # +/- 1.3
MAGGAIN_1_9 = const(0x40)  # +/- 1.9
MAGGAIN_2_5 = const(0x60)  # +/- 2.5
MAGGAIN_4_0 = const(0x80)  # +/- 4.0
MAGGAIN_4_7 = const(0xA0)  # +/- 4.7
MAGGAIN_5_6 = const(0xC0)  # +/- 5.6
MAGGAIN_8_1 = const(0xE0)  # +/- 8.1

# Magentometer rates
MAGRATE_0_7 = const(0x00)  # 0.75 Hz
MAGRATE_1_5 = const(0x01)  # 1.5 Hz
MAGRATE_3_0 = const(0x02)  # 3.0 Hz
MAGRATE_7_5 = const(0x03)  # 7.5 Hz
MAGRATE_15 = const(0x04)  # 15 Hz
MAGRATE_30 = const(0x05)  # 30 Hz
MAGRATE_75 = const(0x06)  # 75 Hz
MAGRATE_220 = const(0x07)  # 220 Hz

# Conversion constants
_GRAVITY_STANDARD = 9.80665  # Earth's gravity in m/s^2
_GAUSS_TO_MICROTESLA = 100.0  # Gauss to micro-Tesla multiplier


class LSM303DLH_Mag:
    """Driver for the Driver for the LSM303DLH's 'magnetometer.

    :param busio.I2C i2c_bus: The I2C bus the LSM303DLH is connected to.

    """

    # Class-level buffer for reading and writing data with the sensor.
    # This reduces memory allocations but means the code is not re-entrant or
    # thread safe!
    _BUFFER = bytearray(6)

    def __init__(self, i2c):
        self._mag_device = I2CDevice(i2c, _ADDRESS_MAG)
        self._write_u8(
            self._mag_device, _REG_MAG_MR_REG_M, 0x00
        )  # Enable the magnetometer
        self._lsm303mag_gauss_lsb_xy = 1100.0
        self._lsm303mag_gauss_lsb_z = 980.0
        self._mag_gain = MAGGAIN_1_3
        self._mag_rate = MAGRATE_0_7

    @property
    def _raw_magnetic(self):
        """The raw magnetometer sensor values.
        A 3-tuple of X, Y, Z axis values that are 16-bit signed integers.
        """
        self._read_bytes(self._mag_device, _REG_MAG_OUT_X_H_M, 6, self._BUFFER)
        raw_values = struct.unpack_from(">hhh", self._BUFFER[0:6])
        return (raw_values[0], raw_values[2], raw_values[1])

    @property
    def magnetic(self):
        """The processed magnetometer sensor values.
        A 3-tuple of X, Y, Z axis values in microteslas that are signed floats.
        """
        mag_x, mag_y, mag_z = self._raw_magnetic
        return (
            mag_x / self._lsm303mag_gauss_lsb_xy * _GAUSS_TO_MICROTESLA,
            mag_y / self._lsm303mag_gauss_lsb_xy * _GAUSS_TO_MICROTESLA,
            mag_z / self._lsm303mag_gauss_lsb_z * _GAUSS_TO_MICROTESLA,
        )

    @property
    def mag_gain(self):
        """The magnetometer's gain."""
        return self._mag_gain

    @mag_gain.setter
    def mag_gain(self, value):
        assert value in (
            MAGGAIN_1_3,
            MAGGAIN_1_9,
            MAGGAIN_2_5,
            MAGGAIN_4_0,
            MAGGAIN_4_7,
            MAGGAIN_5_6,
            MAGGAIN_8_1,
        )

        self._mag_gain = value
        self._write_u8(self._mag_device, _REG_MAG_CRB_REG_M, self._mag_gain)
        if self._mag_gain == MAGGAIN_1_3:
            self._lsm303mag_gauss_lsb_xy = 1100.0
            self._lsm303mag_gauss_lsb_z = 980.0
        elif self._mag_gain == MAGGAIN_1_9:
            self._lsm303mag_gauss_lsb_xy = 855.0
            self._lsm303mag_gauss_lsb_z = 760.0
        elif self._mag_gain == MAGGAIN_2_5:
            self._lsm303mag_gauss_lsb_xy = 670.0
            self._lsm303mag_gauss_lsb_z = 600.0
        elif self._mag_gain == MAGGAIN_4_0:
            self._lsm303mag_gauss_lsb_xy = 450.0
            self._lsm303mag_gauss_lsb_z = 400.0
        elif self._mag_gain == MAGGAIN_4_7:
            self._lsm303mag_gauss_lsb_xy = 400.0
            self._lsm303mag_gauss_lsb_z = 355.0
        elif self._mag_gain == MAGGAIN_5_6:
            self._lsm303mag_gauss_lsb_xy = 330.0
            self._lsm303mag_gauss_lsb_z = 295.0
        elif self._mag_gain == MAGGAIN_8_1:
            self._lsm303mag_gauss_lsb_xy = 230.0
            self._lsm303mag_gauss_lsb_z = 205.0

    @property
    def mag_rate(self):
        """The magnetometer update rate."""
        return self._mag_rate

    @mag_rate.setter
    def mag_rate(self, value):
        assert value in (
            MAGRATE_0_7,
            MAGRATE_1_5,
            MAGRATE_3_0,
            MAGRATE_7_5,
            MAGRATE_15,
            MAGRATE_30,
            MAGRATE_75,
            MAGRATE_220,
        )

        self._mag_rate = value
        reg_m = ((value & 0x07) << 2) & 0xFF
        self._write_u8(self._mag_device, _REG_MAG_CRA_REG_M, reg_m)

    def _read_u8(self, device, address):
        with device as i2c:
            self._BUFFER[0] = address & 0xFF
            i2c.write_then_readinto(self._BUFFER, self._BUFFER, out_end=1, in_end=1)
        return self._BUFFER[0]

    def _write_u8(self, device, address, val):
        with device as i2c:
            self._BUFFER[0] = address & 0xFF
            self._BUFFER[1] = val & 0xFF
            i2c.write(self._BUFFER, end=2)

    @staticmethod
    def _read_bytes(device, address, count, buf):
        with device as i2c:
            buf[0] = address & 0xFF
            i2c.write_then_readinto(buf, buf, out_end=1, in_end=count)
