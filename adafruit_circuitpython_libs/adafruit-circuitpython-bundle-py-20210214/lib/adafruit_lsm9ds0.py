# SPDX-FileCopyrightText: 2017 Tony DiCola for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_lsm9ds0`
====================================================

CircuitPython module for the LSM9DS0 accelerometer, magnetometer, gyroscope.
Based on the driver from:
https://github.com/adafruit/Adafruit_LSM9DS0

See examples/simpletest.py for a demo of the usage.

* Author(s): Tony DiCola

Implementation Notes
--------------------

**Hardware:**

* Adafruit `9-DOF Accel/Mag/Gyro+Temp Breakout Board - LSM9DS0
  <https://www.adafruit.com/product/2021>`_ (Product ID: 2021)

* FLORA `9-DOF Accelerometer/Gyroscope/Magnetometer - LSM9DS0
  <https://www.adafruit.com/product/2020>`_ (Product ID: 2020)

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the ESP8622 and M0-based boards:
  https://github.com/adafruit/circuitpython/releases
* Adafruit's Bus Device library: https://github.com/adafruit/Adafruit_CircuitPython_BusDevice
"""
try:
    import struct
except ImportError:
    import ustruct as struct

import adafruit_bus_device.i2c_device as i2c_device
import adafruit_bus_device.spi_device as spi_device
from digitalio import Direction

from micropython import const

__version__ = "2.2.5"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_LSM9DS0.git"

# Internal constants and register values:
_LSM9DS0_ADDRESS_ACCELMAG = const(0x1D)  # 3B >> 1 = 7bit default
_LSM9DS0_ADDRESS_GYRO = const(0x6B)  # D6 >> 1 = 7bit default
_LSM9DS0_XM_ID = const(0b01001001)
_LSM9DS0_G_ID = const(0b11010100)
_LSM9DS0_ACCEL_MG_LSB_2G = 0.061
_LSM9DS0_ACCEL_MG_LSB_4G = 0.122
_LSM9DS0_ACCEL_MG_LSB_6G = 0.183
_LSM9DS0_ACCEL_MG_LSB_8G = 0.244
_LSM9DS0_ACCEL_MG_LSB_16G = 0.732  # Is this right? Was expecting 0.488
_LSM9DS0_MAG_MGAUSS_2GAUSS = 0.08
_LSM9DS0_MAG_MGAUSS_4GAUSS = 0.16
_LSM9DS0_MAG_MGAUSS_8GAUSS = 0.32
_LSM9DS0_MAG_MGAUSS_12GAUSS = 0.48
_LSM9DS0_GYRO_DPS_DIGIT_245DPS = 0.00875
_LSM9DS0_GYRO_DPS_DIGIT_500DPS = 0.01750
_LSM9DS0_GYRO_DPS_DIGIT_2000DPS = 0.07000
_LSM9DS0_TEMP_LSB_DEGREE_CELSIUS = 8  # 1°C = 8, 25° = 200, etc.
_LSM9DS0_REGISTER_WHO_AM_I_G = const(0x0F)
_LSM9DS0_REGISTER_CTRL_REG1_G = const(0x20)
_LSM9DS0_REGISTER_CTRL_REG3_G = const(0x22)
_LSM9DS0_REGISTER_CTRL_REG4_G = const(0x23)
_LSM9DS0_REGISTER_OUT_X_L_G = const(0x28)
_LSM9DS0_REGISTER_OUT_X_H_G = const(0x29)
_LSM9DS0_REGISTER_OUT_Y_L_G = const(0x2A)
_LSM9DS0_REGISTER_OUT_Y_H_G = const(0x2B)
_LSM9DS0_REGISTER_OUT_Z_L_G = const(0x2C)
_LSM9DS0_REGISTER_OUT_Z_H_G = const(0x2D)
_LSM9DS0_REGISTER_TEMP_OUT_L_XM = const(0x05)
_LSM9DS0_REGISTER_TEMP_OUT_H_XM = const(0x06)
_LSM9DS0_REGISTER_STATUS_REG_M = const(0x07)
_LSM9DS0_REGISTER_OUT_X_L_M = const(0x08)
_LSM9DS0_REGISTER_OUT_X_H_M = const(0x09)
_LSM9DS0_REGISTER_OUT_Y_L_M = const(0x0A)
_LSM9DS0_REGISTER_OUT_Y_H_M = const(0x0B)
_LSM9DS0_REGISTER_OUT_Z_L_M = const(0x0C)
_LSM9DS0_REGISTER_OUT_Z_H_M = const(0x0D)
_LSM9DS0_REGISTER_WHO_AM_I_XM = const(0x0F)
_LSM9DS0_REGISTER_INT_CTRL_REG_M = const(0x12)
_LSM9DS0_REGISTER_INT_SRC_REG_M = const(0x13)
_LSM9DS0_REGISTER_CTRL_REG1_XM = const(0x20)
_LSM9DS0_REGISTER_CTRL_REG2_XM = const(0x21)
_LSM9DS0_REGISTER_CTRL_REG5_XM = const(0x24)
_LSM9DS0_REGISTER_CTRL_REG6_XM = const(0x25)
_LSM9DS0_REGISTER_CTRL_REG7_XM = const(0x26)
_LSM9DS0_REGISTER_OUT_X_L_A = const(0x28)
_LSM9DS0_REGISTER_OUT_X_H_A = const(0x29)
_LSM9DS0_REGISTER_OUT_Y_L_A = const(0x2A)
_LSM9DS0_REGISTER_OUT_Y_H_A = const(0x2B)
_LSM9DS0_REGISTER_OUT_Z_L_A = const(0x2C)
_LSM9DS0_REGISTER_OUT_Z_H_A = const(0x2D)
_GYROTYPE = True
_XMTYPE = False
_SENSORS_GRAVITY_STANDARD = 9.80665

# User facing constants/module globals.
ACCELRANGE_2G = 0b000 << 3
ACCELRANGE_4G = 0b001 << 3
ACCELRANGE_6G = 0b010 << 3
ACCELRANGE_8G = 0b011 << 3
ACCELRANGE_16G = 0b100 << 3
MAGGAIN_2GAUSS = 0b00 << 5  # +/- 2 gauss
MAGGAIN_4GAUSS = 0b01 << 5  # +/- 4 gauss
MAGGAIN_8GAUSS = 0b10 << 5  # +/- 8 gauss
MAGGAIN_12GAUSS = 0b11 << 5  # +/- 12 gauss
GYROSCALE_245DPS = 0b00 << 4  # +/- 245 degrees per second rotation
GYROSCALE_500DPS = 0b01 << 4  # +/- 500 degrees per second rotation
GYROSCALE_2000DPS = 0b10 << 4  # +/- 2000 degrees per second rotation


def _twos_comp(val, bits):
    # Convert an unsigned integer in 2's compliment form of the specified bit
    # length to its signed integer value and return it.
    if val & (1 << (bits - 1)) != 0:
        return val - (1 << bits)
    return val


class LSM9DS0:
    """Driver for the LSM9DS0 accelerometer, magnetometer, gyroscope."""

    # Class-level buffer for reading and writing data with the sensor.
    # This reduces memory allocations but means the code is not re-entrant or
    # thread safe!
    _BUFFER = bytearray(6)

    def __init__(self):
        # Check ID registers.
        if (
            self._read_u8(_XMTYPE, _LSM9DS0_REGISTER_WHO_AM_I_XM) != _LSM9DS0_XM_ID
            or self._read_u8(_GYROTYPE, _LSM9DS0_REGISTER_WHO_AM_I_G) != _LSM9DS0_G_ID
        ):
            raise RuntimeError("Could not find LSM9DS0, check wiring!")
        # Enable the accelerometer continous
        self._write_u8(_XMTYPE, _LSM9DS0_REGISTER_CTRL_REG1_XM, 0x67)
        self._write_u8(_XMTYPE, _LSM9DS0_REGISTER_CTRL_REG5_XM, 0b11110000)
        # enable mag continuous
        self._write_u8(_XMTYPE, _LSM9DS0_REGISTER_CTRL_REG7_XM, 0b00000000)
        # enable gyro continuous
        self._write_u8(_GYROTYPE, _LSM9DS0_REGISTER_CTRL_REG1_G, 0x0F)
        # enable the temperature sensor (output rate same as the mag sensor)
        temp_reg = self._read_u8(_XMTYPE, _LSM9DS0_REGISTER_CTRL_REG5_XM)
        self._write_u8(_XMTYPE, _LSM9DS0_REGISTER_CTRL_REG5_XM, temp_reg | (1 << 7))
        # Set default ranges for the various sensors
        self._accel_mg_lsb = None
        self._mag_mgauss_lsb = None
        self._gyro_dps_digit = None
        self.accel_range = ACCELRANGE_2G
        self.mag_gain = MAGGAIN_2GAUSS
        self.gyro_scale = GYROSCALE_245DPS

    @property
    def accel_range(self):
        """The accelerometer range.  Must be a value of:
        - ACCELRANGE_2G
        - ACCELRANGE_4G
        - ACCELRANGE_6G
        - ACCELRANGE_8G
        - ACCELRANGE_16G
        """
        reg = self._read_u8(_XMTYPE, _LSM9DS0_REGISTER_CTRL_REG2_XM)
        return (reg & 0b00111000) & 0xFF

    @accel_range.setter
    def accel_range(self, val):
        assert val in (
            ACCELRANGE_2G,
            ACCELRANGE_4G,
            ACCELRANGE_6G,
            ACCELRANGE_8G,
            ACCELRANGE_16G,
        )
        reg = self._read_u8(_XMTYPE, _LSM9DS0_REGISTER_CTRL_REG2_XM)
        reg = (reg & ~(0b00111000)) & 0xFF
        reg |= val
        self._write_u8(_XMTYPE, _LSM9DS0_REGISTER_CTRL_REG2_XM, reg)
        if val == ACCELRANGE_2G:
            self._accel_mg_lsb = _LSM9DS0_ACCEL_MG_LSB_2G
        elif val == ACCELRANGE_4G:
            self._accel_mg_lsb = _LSM9DS0_ACCEL_MG_LSB_4G
        elif val == ACCELRANGE_6G:
            self._accel_mg_lsb = _LSM9DS0_ACCEL_MG_LSB_6G
        elif val == ACCELRANGE_8G:
            self._accel_mg_lsb = _LSM9DS0_ACCEL_MG_LSB_8G
        elif val == ACCELRANGE_16G:
            self._accel_mg_lsb = _LSM9DS0_ACCEL_MG_LSB_16G

    @property
    def mag_gain(self):
        """The magnetometer gain.  Must be a value of:
        - MAGGAIN_2GAUSS
        - MAGGAIN_4GAUSS
        - MAGGAIN_8GAUSS
        - MAGGAIN_12GAUSS
        """
        reg = self._read_u8(_XMTYPE, _LSM9DS0_REGISTER_CTRL_REG6_XM)
        return (reg & 0b01100000) & 0xFF

    @mag_gain.setter
    def mag_gain(self, val):
        assert val in (MAGGAIN_2GAUSS, MAGGAIN_4GAUSS, MAGGAIN_8GAUSS, MAGGAIN_12GAUSS)
        reg = self._read_u8(_XMTYPE, _LSM9DS0_REGISTER_CTRL_REG6_XM)
        reg = (reg & ~(0b01100000)) & 0xFF
        reg |= val
        self._write_u8(_XMTYPE, _LSM9DS0_REGISTER_CTRL_REG6_XM, reg)
        if val == MAGGAIN_2GAUSS:
            self._mag_mgauss_lsb = _LSM9DS0_MAG_MGAUSS_2GAUSS
        elif val == MAGGAIN_4GAUSS:
            self._mag_mgauss_lsb = _LSM9DS0_MAG_MGAUSS_4GAUSS
        elif val == MAGGAIN_8GAUSS:
            self._mag_mgauss_lsb = _LSM9DS0_MAG_MGAUSS_8GAUSS
        elif val == MAGGAIN_12GAUSS:
            self._mag_mgauss_lsb = _LSM9DS0_MAG_MGAUSS_12GAUSS

    @property
    def gyro_scale(self):
        """The gyroscope scale.  Must be a value of:
        - GYROSCALE_245DPS
        - GYROSCALE_500DPS
        - GYROSCALE_2000DPS
        """
        reg = self._read_u8(_GYROTYPE, _LSM9DS0_REGISTER_CTRL_REG4_G)
        return (reg & 0b00110000) & 0xFF

    @gyro_scale.setter
    def gyro_scale(self, val):
        assert val in (GYROSCALE_245DPS, GYROSCALE_500DPS, GYROSCALE_2000DPS)
        reg = self._read_u8(_GYROTYPE, _LSM9DS0_REGISTER_CTRL_REG4_G)
        reg = (reg & ~(0b00110000)) & 0xFF
        reg |= val
        self._write_u8(_GYROTYPE, _LSM9DS0_REGISTER_CTRL_REG4_G, reg)
        if val == GYROSCALE_245DPS:
            self._gyro_dps_digit = _LSM9DS0_GYRO_DPS_DIGIT_245DPS
        elif val == GYROSCALE_500DPS:
            self._gyro_dps_digit = _LSM9DS0_GYRO_DPS_DIGIT_500DPS
        elif val == GYROSCALE_2000DPS:
            self._gyro_dps_digit = _LSM9DS0_GYRO_DPS_DIGIT_2000DPS

    def read_accel_raw(self):
        """Read the raw accelerometer sensor values and return it as a
        3-tuple of X, Y, Z axis values that are 16-bit unsigned values.  If you
        want the acceleration in nice units you probably want to use the
        accelerometer property!
        """
        # Read the accelerometer
        self._read_bytes(_XMTYPE, 0x80 | _LSM9DS0_REGISTER_OUT_X_L_A, 6, self._BUFFER)
        raw_x, raw_y, raw_z = struct.unpack_from("<hhh", self._BUFFER[0:6])
        return (raw_x, raw_y, raw_z)

    @property
    def acceleration(self):
        """The accelerometer X, Y, Z axis values as a 3-tuple of
        m/s^2 values.
        """
        raw = self.read_accel_raw()
        return (
            x * self._accel_mg_lsb / 1000.0 * _SENSORS_GRAVITY_STANDARD for x in raw
        )

    def read_mag_raw(self):
        """Read the raw magnetometer sensor values and return it as a
        3-tuple of X, Y, Z axis values that are 16-bit unsigned values.  If you
        want the magnetometer in nice units you probably want to use the
        magnetometer property!
        """
        # Read the magnetometer
        self._read_bytes(_XMTYPE, 0x80 | _LSM9DS0_REGISTER_OUT_X_L_M, 6, self._BUFFER)
        raw_x, raw_y, raw_z = struct.unpack_from("<hhh", self._BUFFER[0:6])
        return (raw_x, raw_y, raw_z)

    @property
    def magnetic(self):
        """The magnetometer X, Y, Z axis values as a 3-tuple of
        gauss values.
        """
        raw = self.read_mag_raw()
        return (x * self._mag_mgauss_lsb / 1000.0 for x in raw)

    def read_gyro_raw(self):
        """Read the raw gyroscope sensor values and return it as a
        3-tuple of X, Y, Z axis values that are 16-bit unsigned values.  If you
        want the gyroscope in nice units you probably want to use the
        gyroscope property!
        """
        # Read the gyroscope
        self._read_bytes(_GYROTYPE, 0x80 | _LSM9DS0_REGISTER_OUT_X_L_G, 6, self._BUFFER)
        raw_x, raw_y, raw_z = struct.unpack_from("<hhh", self._BUFFER[0:6])
        return (raw_x, raw_y, raw_z)

    @property
    def gyro(self):
        """The gyroscope X, Y, Z axis values as a 3-tuple of
        degrees/second values.
        """
        raw = self.read_gyro_raw()
        return (x * self._gyro_dps_digit for x in raw)

    def read_temp_raw(self):
        """Read the raw temperature sensor value and return it as a 16-bit
        unsigned value.  If you want the temperature in nice units you probably
        want to use the temperature property!
        """
        # Read temp sensor
        self._read_bytes(
            _XMTYPE, 0x80 | _LSM9DS0_REGISTER_TEMP_OUT_L_XM, 2, self._BUFFER
        )
        temp = ((self._BUFFER[1] << 8) | self._BUFFER[0]) >> 4
        return _twos_comp(temp, 12)

    @property
    def temperature(self):
        """The temperature of the sensor in degrees Celsius."""
        # This is just a guess since the starting point (21C here) isn't documented :(
        temp = self.read_temp_raw()
        temp = 21.0 + temp / 8
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


class LSM9DS0_I2C(LSM9DS0):
    """Driver for the LSM9DS0 connected over I2C."""

    def __init__(self, i2c):
        self._gyro_device = i2c_device.I2CDevice(i2c, _LSM9DS0_ADDRESS_GYRO)
        self._xm_device = i2c_device.I2CDevice(i2c, _LSM9DS0_ADDRESS_ACCELMAG)
        super().__init__()

    def _read_u8(self, sensor_type, address):
        self._read_bytes(sensor_type, address, 1, self._BUFFER)
        return self._BUFFER[0]

    def _read_bytes(self, sensor_type, address, count, buf):
        if sensor_type == _GYROTYPE:
            device = self._gyro_device
        else:
            device = self._xm_device
        with device as i2c:
            buf[0] = address & 0xFF
            i2c.write(buf, end=1)
            i2c.readinto(buf, end=count)
        # print("read from %02x: %s" % (address, [hex(i) for i in buf[:count]]))

    def _write_u8(self, sensor_type, address, val):
        if sensor_type == _GYROTYPE:
            device = self._gyro_device
        else:
            device = self._xm_device
        with device as i2c:
            self._BUFFER[0] = address & 0xFF
            self._BUFFER[1] = val & 0xFF
            i2c.write(self._BUFFER, end=2)
        # print("write to %02x: %02x" % (address, val))


class LSM9DS0_SPI(LSM9DS0):
    """Driver for the LSM9DS0 connected over SPI."""

    # pylint: disable=no-member
    def __init__(self, spi, xmcs, gcs):
        gcs.direction = Direction.OUTPUT
        gcs.value = True
        xmcs.direction = Direction.OUTPUT
        xmcs.value = True
        self._gyro_device = spi_device.SPIDevice(spi, gcs)
        self._xm_device = spi_device.SPIDevice(spi, xmcs)
        super().__init__()

    def _read_u8(self, sensor_type, address):
        self._read_bytes(sensor_type, address, 1, self._BUFFER)
        return self._BUFFER[0]

    def _read_bytes(self, sensor_type, address, count, buf):
        if sensor_type == _GYROTYPE:
            device = self._gyro_device
        else:
            device = self._xm_device
        with device as spi:
            buf[0] = (address | 0x80 | 0x40) & 0xFF
            spi.write(buf, end=1)
            spi.readinto(buf, end=count)
        # print("read from %02x: %s" % (address, [hex(i) for i in buf[:count]]))

    def _write_u8(self, sensor_type, address, val):
        if sensor_type == _GYROTYPE:
            device = self._gyro_device
        else:
            device = self._xm_device
        with device as spi:
            self._BUFFER[0] = (address & 0x7F) & 0xFF
            self._BUFFER[1] = val & 0xFF
            spi.write(self._BUFFER, end=2)
        # print("write to %02x: %02x" % (address, val))
