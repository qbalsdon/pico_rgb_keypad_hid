# SPDX-FileCopyrightText: 2017 Tony DiCola for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_lsm9ds1`
====================================================

CircuitPython module for the LSM9DS1 accelerometer, magnetometer, gyroscope.
Based on the driver from:
https://github.com/adafruit/Adafruit_LSM9DS1

See examples/simpletest.py for a demo of the usage.

* Author(s): Tony DiCola

Implementation Notes
--------------------

**Hardware:**

* Adafruit `9-DOF Accel/Mag/Gyro+Temp Breakout Board - LSM9DS1
  <https://www.adafruit.com/product/3387>`_ (Product ID: 3387)

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the ESP8622 and M0-based boards:
  https://github.com/adafruit/circuitpython/releases
* Adafruit's Bus Device library: https://github.com/adafruit/Adafruit_CircuitPython_BusDevice
"""

__version__ = "2.1.6"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_LSM9DS1.git"

import time

try:
    import struct
except ImportError:
    import ustruct as struct

import adafruit_bus_device.i2c_device as i2c_device
import adafruit_bus_device.spi_device as spi_device
from micropython import const

# Internal constants and register values:
_LSM9DS1_ADDRESS_ACCELGYRO = const(0x6B)
_LSM9DS1_ADDRESS_MAG = const(0x1E)
_LSM9DS1_XG_ID = const(0b01101000)
_LSM9DS1_MAG_ID = const(0b00111101)
_LSM9DS1_ACCEL_MG_LSB_2G = 0.061
_LSM9DS1_ACCEL_MG_LSB_4G = 0.122
_LSM9DS1_ACCEL_MG_LSB_8G = 0.244
_LSM9DS1_ACCEL_MG_LSB_16G = 0.732
_LSM9DS1_MAG_MGAUSS_4GAUSS = 0.14
_LSM9DS1_MAG_MGAUSS_8GAUSS = 0.29
_LSM9DS1_MAG_MGAUSS_12GAUSS = 0.43
_LSM9DS1_MAG_MGAUSS_16GAUSS = 0.58
_LSM9DS1_GYRO_DPS_DIGIT_245DPS = 0.00875
_LSM9DS1_GYRO_DPS_DIGIT_500DPS = 0.01750
_LSM9DS1_GYRO_DPS_DIGIT_2000DPS = 0.07000
_LSM9DS1_TEMP_LSB_DEGREE_CELSIUS = 8  # 1°C = 8, 25° = 200, etc.
_LSM9DS1_REGISTER_WHO_AM_I_XG = const(0x0F)
_LSM9DS1_REGISTER_CTRL_REG1_G = const(0x10)
_LSM9DS1_REGISTER_CTRL_REG2_G = const(0x11)
_LSM9DS1_REGISTER_CTRL_REG3_G = const(0x12)
_LSM9DS1_REGISTER_TEMP_OUT_L = const(0x15)
_LSM9DS1_REGISTER_TEMP_OUT_H = const(0x16)
_LSM9DS1_REGISTER_STATUS_REG = const(0x17)
_LSM9DS1_REGISTER_OUT_X_L_G = const(0x18)
_LSM9DS1_REGISTER_OUT_X_H_G = const(0x19)
_LSM9DS1_REGISTER_OUT_Y_L_G = const(0x1A)
_LSM9DS1_REGISTER_OUT_Y_H_G = const(0x1B)
_LSM9DS1_REGISTER_OUT_Z_L_G = const(0x1C)
_LSM9DS1_REGISTER_OUT_Z_H_G = const(0x1D)
_LSM9DS1_REGISTER_CTRL_REG4 = const(0x1E)
_LSM9DS1_REGISTER_CTRL_REG5_XL = const(0x1F)
_LSM9DS1_REGISTER_CTRL_REG6_XL = const(0x20)
_LSM9DS1_REGISTER_CTRL_REG7_XL = const(0x21)
_LSM9DS1_REGISTER_CTRL_REG8 = const(0x22)
_LSM9DS1_REGISTER_CTRL_REG9 = const(0x23)
_LSM9DS1_REGISTER_CTRL_REG10 = const(0x24)
_LSM9DS1_REGISTER_OUT_X_L_XL = const(0x28)
_LSM9DS1_REGISTER_OUT_X_H_XL = const(0x29)
_LSM9DS1_REGISTER_OUT_Y_L_XL = const(0x2A)
_LSM9DS1_REGISTER_OUT_Y_H_XL = const(0x2B)
_LSM9DS1_REGISTER_OUT_Z_L_XL = const(0x2C)
_LSM9DS1_REGISTER_OUT_Z_H_XL = const(0x2D)
_LSM9DS1_REGISTER_WHO_AM_I_M = const(0x0F)
_LSM9DS1_REGISTER_CTRL_REG1_M = const(0x20)
_LSM9DS1_REGISTER_CTRL_REG2_M = const(0x21)
_LSM9DS1_REGISTER_CTRL_REG3_M = const(0x22)
_LSM9DS1_REGISTER_CTRL_REG4_M = const(0x23)
_LSM9DS1_REGISTER_CTRL_REG5_M = const(0x24)
_LSM9DS1_REGISTER_STATUS_REG_M = const(0x27)
_LSM9DS1_REGISTER_OUT_X_L_M = const(0x28)
_LSM9DS1_REGISTER_OUT_X_H_M = const(0x29)
_LSM9DS1_REGISTER_OUT_Y_L_M = const(0x2A)
_LSM9DS1_REGISTER_OUT_Y_H_M = const(0x2B)
_LSM9DS1_REGISTER_OUT_Z_L_M = const(0x2C)
_LSM9DS1_REGISTER_OUT_Z_H_M = const(0x2D)
_LSM9DS1_REGISTER_CFG_M = const(0x30)
_LSM9DS1_REGISTER_INT_SRC_M = const(0x31)
_MAGTYPE = True
_XGTYPE = False
_SENSORS_GRAVITY_STANDARD = 9.80665
_SPI_AUTO_INCR = 0x40

# User facing constants/module globals.
ACCELRANGE_2G = 0b00 << 3
ACCELRANGE_16G = 0b01 << 3
ACCELRANGE_4G = 0b10 << 3
ACCELRANGE_8G = 0b11 << 3
MAGGAIN_4GAUSS = 0b00 << 5  # +/- 4 gauss
MAGGAIN_8GAUSS = 0b01 << 5  # +/- 8 gauss
MAGGAIN_12GAUSS = 0b10 << 5  # +/- 12 gauss
MAGGAIN_16GAUSS = 0b11 << 5  # +/- 16 gauss
GYROSCALE_245DPS = 0b00 << 3  # +/- 245 degrees/s rotation
GYROSCALE_500DPS = 0b01 << 3  # +/- 500 degrees/s rotation
GYROSCALE_2000DPS = 0b11 << 3  # +/- 2000 degrees/s rotation


def _twos_comp(val, bits):
    # Convert an unsigned integer in 2's compliment form of the specified bit
    # length to its signed integer value and return it.
    if val & (1 << (bits - 1)) != 0:
        return val - (1 << bits)
    return val


class LSM9DS1:
    """Driver for the LSM9DS1 accelerometer, magnetometer, gyroscope."""

    # Class-level buffer for reading and writing data with the sensor.
    # This reduces memory allocations but means the code is not re-entrant or
    # thread safe!
    _BUFFER = bytearray(6)

    def __init__(self):
        # soft reset & reboot accel/gyro
        self._write_u8(_XGTYPE, _LSM9DS1_REGISTER_CTRL_REG8, 0x05)
        # soft reset & reboot magnetometer
        self._write_u8(_MAGTYPE, _LSM9DS1_REGISTER_CTRL_REG2_M, 0x0C)
        time.sleep(0.01)
        # Check ID registers.
        if (
            self._read_u8(_XGTYPE, _LSM9DS1_REGISTER_WHO_AM_I_XG) != _LSM9DS1_XG_ID
            or self._read_u8(_MAGTYPE, _LSM9DS1_REGISTER_WHO_AM_I_M) != _LSM9DS1_MAG_ID
        ):
            raise RuntimeError("Could not find LSM9DS1, check wiring!")
        # enable gyro continuous
        self._write_u8(_XGTYPE, _LSM9DS1_REGISTER_CTRL_REG1_G, 0xC0)  # on XYZ
        # Enable the accelerometer continous
        self._write_u8(_XGTYPE, _LSM9DS1_REGISTER_CTRL_REG5_XL, 0x38)
        self._write_u8(_XGTYPE, _LSM9DS1_REGISTER_CTRL_REG6_XL, 0xC0)
        # enable mag continuous
        self._write_u8(_MAGTYPE, _LSM9DS1_REGISTER_CTRL_REG3_M, 0x00)
        # Set default ranges for the various sensors
        self._accel_mg_lsb = None
        self._mag_mgauss_lsb = None
        self._gyro_dps_digit = None
        self.accel_range = ACCELRANGE_2G
        self.mag_gain = MAGGAIN_4GAUSS
        self.gyro_scale = GYROSCALE_245DPS

    @property
    def accel_range(self):
        """The accelerometer range.  Must be a value of:
        - ACCELRANGE_2G
        - ACCELRANGE_4G
        - ACCELRANGE_8G
        - ACCELRANGE_16G
        """
        reg = self._read_u8(_XGTYPE, _LSM9DS1_REGISTER_CTRL_REG6_XL)
        return (reg & 0b00011000) & 0xFF

    @accel_range.setter
    def accel_range(self, val):
        assert val in (ACCELRANGE_2G, ACCELRANGE_4G, ACCELRANGE_8G, ACCELRANGE_16G)
        reg = self._read_u8(_XGTYPE, _LSM9DS1_REGISTER_CTRL_REG6_XL)
        reg = (reg & ~(0b00011000)) & 0xFF
        reg |= val
        self._write_u8(_XGTYPE, _LSM9DS1_REGISTER_CTRL_REG6_XL, reg)
        if val == ACCELRANGE_2G:
            self._accel_mg_lsb = _LSM9DS1_ACCEL_MG_LSB_2G
        elif val == ACCELRANGE_4G:
            self._accel_mg_lsb = _LSM9DS1_ACCEL_MG_LSB_4G
        elif val == ACCELRANGE_8G:
            self._accel_mg_lsb = _LSM9DS1_ACCEL_MG_LSB_8G
        elif val == ACCELRANGE_16G:
            self._accel_mg_lsb = _LSM9DS1_ACCEL_MG_LSB_16G

    @property
    def mag_gain(self):
        """The magnetometer gain.  Must be a value of:
        - MAGGAIN_4GAUSS
        - MAGGAIN_8GAUSS
        - MAGGAIN_12GAUSS
        - MAGGAIN_16GAUSS
        """
        reg = self._read_u8(_MAGTYPE, _LSM9DS1_REGISTER_CTRL_REG2_M)
        return (reg & 0b01100000) & 0xFF

    @mag_gain.setter
    def mag_gain(self, val):
        assert val in (MAGGAIN_4GAUSS, MAGGAIN_8GAUSS, MAGGAIN_12GAUSS, MAGGAIN_16GAUSS)
        reg = self._read_u8(_MAGTYPE, _LSM9DS1_REGISTER_CTRL_REG2_M)
        reg = (reg & ~(0b01100000)) & 0xFF
        reg |= val
        self._write_u8(_MAGTYPE, _LSM9DS1_REGISTER_CTRL_REG2_M, reg)
        if val == MAGGAIN_4GAUSS:
            self._mag_mgauss_lsb = _LSM9DS1_MAG_MGAUSS_4GAUSS
        elif val == MAGGAIN_8GAUSS:
            self._mag_mgauss_lsb = _LSM9DS1_MAG_MGAUSS_8GAUSS
        elif val == MAGGAIN_12GAUSS:
            self._mag_mgauss_lsb = _LSM9DS1_MAG_MGAUSS_12GAUSS
        elif val == MAGGAIN_16GAUSS:
            self._mag_mgauss_lsb = _LSM9DS1_MAG_MGAUSS_16GAUSS

    @property
    def gyro_scale(self):
        """The gyroscope scale.  Must be a value of:
        - GYROSCALE_245DPS
        - GYROSCALE_500DPS
        - GYROSCALE_2000DPS
        """
        reg = self._read_u8(_XGTYPE, _LSM9DS1_REGISTER_CTRL_REG1_G)
        return (reg & 0b00011000) & 0xFF

    @gyro_scale.setter
    def gyro_scale(self, val):
        assert val in (GYROSCALE_245DPS, GYROSCALE_500DPS, GYROSCALE_2000DPS)
        reg = self._read_u8(_XGTYPE, _LSM9DS1_REGISTER_CTRL_REG1_G)
        reg = (reg & ~(0b00011000)) & 0xFF
        reg |= val
        self._write_u8(_XGTYPE, _LSM9DS1_REGISTER_CTRL_REG1_G, reg)
        if val == GYROSCALE_245DPS:
            self._gyro_dps_digit = _LSM9DS1_GYRO_DPS_DIGIT_245DPS
        elif val == GYROSCALE_500DPS:
            self._gyro_dps_digit = _LSM9DS1_GYRO_DPS_DIGIT_500DPS
        elif val == GYROSCALE_2000DPS:
            self._gyro_dps_digit = _LSM9DS1_GYRO_DPS_DIGIT_2000DPS

    def read_accel_raw(self):
        """Read the raw accelerometer sensor values and return it as a
        3-tuple of X, Y, Z axis values that are 16-bit unsigned values.  If you
        want the acceleration in nice units you probably want to use the
        accelerometer property!
        """
        # Read the accelerometer
        self._read_bytes(_XGTYPE, 0x80 | _LSM9DS1_REGISTER_OUT_X_L_XL, 6, self._BUFFER)
        raw_x, raw_y, raw_z = struct.unpack_from("<hhh", self._BUFFER[0:6])
        return (raw_x, raw_y, raw_z)

    @property
    def acceleration(self):
        """The accelerometer X, Y, Z axis values as a 3-tuple of
        m/s^2 values.
        """
        raw = self.read_accel_raw()
        return map(
            lambda x: x * self._accel_mg_lsb / 1000.0 * _SENSORS_GRAVITY_STANDARD, raw
        )

    def read_mag_raw(self):
        """Read the raw magnetometer sensor values and return it as a
        3-tuple of X, Y, Z axis values that are 16-bit unsigned values.  If you
        want the magnetometer in nice units you probably want to use the
        magnetometer property!
        """
        # Read the magnetometer
        self._read_bytes(_MAGTYPE, 0x80 | _LSM9DS1_REGISTER_OUT_X_L_M, 6, self._BUFFER)
        raw_x, raw_y, raw_z = struct.unpack_from("<hhh", self._BUFFER[0:6])
        return (raw_x, raw_y, raw_z)

    @property
    def magnetic(self):
        """The magnetometer X, Y, Z axis values as a 3-tuple of
        gauss values.
        """
        raw = self.read_mag_raw()
        return map(lambda x: x * self._mag_mgauss_lsb / 1000.0, raw)

    def read_gyro_raw(self):
        """Read the raw gyroscope sensor values and return it as a
        3-tuple of X, Y, Z axis values that are 16-bit unsigned values.  If you
        want the gyroscope in nice units you probably want to use the
        gyroscope property!
        """
        # Read the gyroscope
        self._read_bytes(_XGTYPE, 0x80 | _LSM9DS1_REGISTER_OUT_X_L_G, 6, self._BUFFER)
        raw_x, raw_y, raw_z = struct.unpack_from("<hhh", self._BUFFER[0:6])
        return (raw_x, raw_y, raw_z)

    @property
    def gyro(self):
        """The gyroscope X, Y, Z axis values as a 3-tuple of
        degrees/second values.
        """
        raw = self.read_gyro_raw()
        return map(lambda x: x * self._gyro_dps_digit, raw)

    def read_temp_raw(self):
        """Read the raw temperature sensor value and return it as a 12-bit
        signed value.  If you want the temperature in nice units you probably
        want to use the temperature property!
        """
        # Read temp sensor
        self._read_bytes(_XGTYPE, 0x80 | _LSM9DS1_REGISTER_TEMP_OUT_L, 2, self._BUFFER)
        temp = ((self._BUFFER[1] << 8) | self._BUFFER[0]) >> 4
        return _twos_comp(temp, 12)

    @property
    def temperature(self):
        """The temperature of the sensor in degrees Celsius."""
        # This is just a guess since the starting point (21C here) isn't documented :(
        # See discussion from:
        #  https://github.com/kriswiner/LSM9DS1/issues/3
        temp = self.read_temp_raw()
        temp = 27.5 + temp / 16
        return temp

    def _read_u8(self, sensor_type, address):
        # Read an 8-bit unsigned value from the specified 8-bit address.
        # The sensor_type boolean should be _MAGTYPE when talking to the
        # magnetometer, or _XGTYPE when talking to the accel or gyro.
        # MUST be implemented by subclasses!
        raise NotImplementedError()

    def _read_bytes(self, sensor_type, address, count, buf):
        # Read a count number of bytes into buffer from the provided 8-bit
        # register address.  The sensor_type boolean should be _MAGTYPE when
        # talking to the magnetometer, or _XGTYPE when talking to the accel or
        # gyro.  MUST be implemented by subclasses!
        raise NotImplementedError()

    def _write_u8(self, sensor_type, address, val):
        # Write an 8-bit unsigned value to the specified 8-bit address.
        # The sensor_type boolean should be _MAGTYPE when talking to the
        # magnetometer, or _XGTYPE when talking to the accel or gyro.
        # MUST be implemented by subclasses!
        raise NotImplementedError()


class LSM9DS1_I2C(LSM9DS1):
    """Driver for the LSM9DS1 connect over I2C.

    :param ~busio.I2C i2c: The I2C bus object used to connect to the LSM9DS1.

        .. note:: This object should be shared among other driver classes that use the
            same I2C bus (SDA & SCL pins) to connect to different I2C devices.

    :param int mag_address: A 8-bit integer that represents the i2c address of the
        LSM9DS1's magnetometer. Options are limited to ``0x1C`` or ``0x1E``.
        Defaults to ``0x1E``.

    :param int xg_address: A 8-bit integer that represents the i2c address of the
        LSM9DS1's accelerometer and gyroscope. Options are limited to ``0x6A`` or ``0x6B``.
        Defaults to ``0x6B``.

    """

    def __init__(
        self,
        i2c,
        mag_address=_LSM9DS1_ADDRESS_MAG,
        xg_address=_LSM9DS1_ADDRESS_ACCELGYRO,
    ):
        if mag_address in (0x1C, 0x1E) and xg_address in (0x6A, 0x6B):
            self._mag_device = i2c_device.I2CDevice(i2c, mag_address)
            self._xg_device = i2c_device.I2CDevice(i2c, xg_address)
            super().__init__()
        else:
            raise ValueError(
                "address parmeters are incorrect. Read the docs at "
                "circuitpython.rtfd.io/projects/lsm9ds1/en/latest"
                "/api.html#adafruit_lsm9ds1.LSM9DS1_I2C"
            )

    def _read_u8(self, sensor_type, address):
        if sensor_type == _MAGTYPE:
            device = self._mag_device
        else:
            device = self._xg_device
        with device as i2c:
            self._BUFFER[0] = address & 0xFF
            i2c.write_then_readinto(
                self._BUFFER, self._BUFFER, out_end=1, in_start=1, in_end=2
            )
        return self._BUFFER[1]

    def _read_bytes(self, sensor_type, address, count, buf):
        if sensor_type == _MAGTYPE:
            device = self._mag_device
        else:
            device = self._xg_device
        with device as i2c:
            buf[0] = address & 0xFF
            i2c.write_then_readinto(buf, buf, out_end=1, in_end=count)

    def _write_u8(self, sensor_type, address, val):
        if sensor_type == _MAGTYPE:
            device = self._mag_device
        else:
            device = self._xg_device
        with device as i2c:
            self._BUFFER[0] = address & 0xFF
            self._BUFFER[1] = val & 0xFF
            i2c.write(self._BUFFER, end=2)


class LSM9DS1_SPI(LSM9DS1):
    """Driver for the LSM9DS1 connect over SPI.

    :param ~busio.SPI spi: The SPI bus object used to connect to the LSM9DS1.

        .. note:: This object should be shared among other driver classes that use the
            same SPI bus (SCK, MISO, MOSI pins) to connect to different SPI devices.

    :param ~digitalio.DigitalInOut mcs: The digital output pin connected to the
        LSM9DS1's CSM (Chip Select Magnetometer) pin.

    :param ~digitalio.DigitalInOut xgcs: The digital output pin connected to the
        LSM9DS1's CSAG (Chip Select Accelerometer/Gyroscope) pin.

    """

    # pylint: disable=no-member
    def __init__(self, spi, xgcs, mcs):
        self._mag_device = spi_device.SPIDevice(
            spi, mcs, baudrate=200000, phase=1, polarity=1
        )
        self._xg_device = spi_device.SPIDevice(
            spi, xgcs, baudrate=200000, phase=1, polarity=1
        )
        super().__init__()

    def _read_u8(self, sensor_type, address):
        if sensor_type == _MAGTYPE:
            device = self._mag_device
        else:
            device = self._xg_device
        with device as spi:
            self._BUFFER[0] = (address | 0x80) & 0xFF
            spi.write(self._BUFFER, end=1)
            spi.readinto(self._BUFFER, end=1)
        return self._BUFFER[0]

    def _read_bytes(self, sensor_type, address, count, buf):
        if sensor_type == _MAGTYPE:
            device = self._mag_device
            address |= _SPI_AUTO_INCR
        else:
            device = self._xg_device
        with device as spi:
            buf[0] = (address | 0x80) & 0xFF
            spi.write(buf, end=1)
            spi.readinto(buf, end=count)

    def _write_u8(self, sensor_type, address, val):
        if sensor_type == _MAGTYPE:
            device = self._mag_device
        else:
            device = self._xg_device
        with device as spi:
            self._BUFFER[0] = (address & 0x7F) & 0xFF
            self._BUFFER[1] = val & 0xFF
            spi.write(self._BUFFER, end=2)
