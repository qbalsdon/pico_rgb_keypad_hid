# SPDX-FileCopyrightText: 2017 Tony DiCola for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_mpl3115a2`
====================================================

CircuitPython module for the MPL3115A2 barometric pressure & temperature sensor.
See examples/simpletest.py for a demo of the usage.

* Author(s): Tony DiCola
"""
import time

from micropython import const

try:
    import ustruct as struct
except ImportError:
    import struct

import adafruit_bus_device.i2c_device as i2c_device


__version__ = "1.2.5"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_MPL3115A2.git"


# Internal constants:
_MPL3115A2_ADDRESS = const(0x60)
_MPL3115A2_REGISTER_STATUS = const(0x00)
_MPL3115A2_REGISTER_PRESSURE_MSB = const(0x01)
_MPL3115A2_REGISTER_PRESSURE_CSB = const(0x02)
_MPL3115A2_REGISTER_PRESSURE_LSB = const(0x03)
_MPL3115A2_REGISTER_TEMP_MSB = const(0x04)
_MPL3115A2_REGISTER_TEMP_LSB = const(0x05)
_MPL3115A2_REGISTER_DR_STATUS = const(0x06)
_MPL3115A2_OUT_P_DELTA_MSB = const(0x07)
_MPL3115A2_OUT_P_DELTA_CSB = const(0x08)
_MPL3115A2_OUT_P_DELTA_LSB = const(0x09)
_MPL3115A2_OUT_T_DELTA_MSB = const(0x0A)
_MPL3115A2_OUT_T_DELTA_LSB = const(0x0B)
_MPL3115A2_WHOAMI = const(0x0C)
_MPL3115A2_BAR_IN_MSB = const(0x14)
_MPL3115A2_BAR_IN_LSB = const(0x15)

_MPL3115A2_REGISTER_STATUS_TDR = const(0x02)
_MPL3115A2_REGISTER_STATUS_PDR = const(0x04)
_MPL3115A2_REGISTER_STATUS_PTDR = const(0x08)

_MPL3115A2_PT_DATA_CFG = const(0x13)
_MPL3115A2_PT_DATA_CFG_TDEFE = const(0x01)
_MPL3115A2_PT_DATA_CFG_PDEFE = const(0x02)
_MPL3115A2_PT_DATA_CFG_DREM = const(0x04)

_MPL3115A2_CTRL_REG1 = const(0x26)
_MPL3115A2_CTRL_REG2 = const(0x27)
_MPL3115A2_CTRL_REG3 = const(0x28)
_MPL3115A2_CTRL_REG4 = const(0x29)
_MPL3115A2_CTRL_REG5 = const(0x2A)

_MPL3115A2_CTRL_REG1_SBYB = const(0x01)
_MPL3115A2_CTRL_REG1_OST = const(0x02)
_MPL3115A2_CTRL_REG1_RST = const(0x04)
_MPL3115A2_CTRL_REG1_RAW = const(0x40)
_MPL3115A2_CTRL_REG1_ALT = const(0x80)
_MPL3115A2_CTRL_REG1_BAR = const(0x00)

_MPL3115A2_CTRL_REG1_OS1 = const(0x00)
_MPL3115A2_CTRL_REG1_OS2 = const(0x08)
_MPL3115A2_CTRL_REG1_OS4 = const(0x10)
_MPL3115A2_CTRL_REG1_OS8 = const(0x18)
_MPL3115A2_CTRL_REG1_OS16 = const(0x20)
_MPL3115A2_CTRL_REG1_OS32 = const(0x28)
_MPL3115A2_CTRL_REG1_OS64 = const(0x30)
_MPL3115A2_CTRL_REG1_OS128 = const(0x38)

_MPL3115A2_REGISTER_STARTCONVERSION = const(0x12)


class MPL3115A2:
    """Instance of the MPL3115A2 sensor.  Must specify the following parameters
    when creating an instance of this device:
    - i2c: The I2C bus connected to the sensor.

    In addition you can specify the following optional keyword arguments:
    - address: The I2C address of the device if it's different from the default.
    """

    # Class level buffer to reduce memory usage and allocations.
    # Note this is not thread safe by design!
    _BUFFER = bytearray(4)

    def __init__(self, i2c, *, address=_MPL3115A2_ADDRESS):
        self._device = i2c_device.I2CDevice(i2c, address)
        # Validate the chip ID.
        if self._read_u8(_MPL3115A2_WHOAMI) != 0xC4:
            raise RuntimeError("Failed to find MPL3115A2, check your wiring!")
        # Reset.  Note the chip immediately resets and won't send an I2C back
        # so we need to catch the OSError and swallow it (otherwise this fails
        # expecting an ACK that never comes).
        try:
            self._write_u8(_MPL3115A2_CTRL_REG1, _MPL3115A2_CTRL_REG1_RST)
        except OSError:
            pass
        time.sleep(0.01)
        # Poll for the reset to finish.
        self._poll_reg1(_MPL3115A2_CTRL_REG1_RST)
        # Configure the chip registers with default values.
        self._ctrl_reg1 = _MPL3115A2_CTRL_REG1_OS128 | _MPL3115A2_CTRL_REG1_ALT
        self._write_u8(_MPL3115A2_CTRL_REG1, self._ctrl_reg1)
        self._write_u8(
            _MPL3115A2_PT_DATA_CFG,
            _MPL3115A2_PT_DATA_CFG_TDEFE
            | _MPL3115A2_PT_DATA_CFG_PDEFE
            | _MPL3115A2_PT_DATA_CFG_DREM,
        )

    def _read_into(self, address, buf, count=None):
        # Read bytes from the specified 8-bit address into the provided buffer.
        # If the count is not specified then the entire buffer is filled,
        # otherwise count bytes are copied in.
        if count is None:
            count = len(buf)
        with self._device as i2c:
            i2c.write_then_readinto(bytes([address & 0xFF]), buf, in_end=count)

    def _read_u8(self, address):
        # Read an 8-bit unsigned value from the specified 8-bit address.
        self._read_into(address, self._BUFFER, count=1)
        return self._BUFFER[0]

    def _write_u8(self, address, val):
        # Write an 8-bit unsigned value to the specified 8-bit address.
        with self._device as i2c:
            self._BUFFER[0] = address & 0xFF
            self._BUFFER[1] = val & 0xFF
            i2c.write(self._BUFFER, end=2)

    def _write_u16_be(self, address, val):
        # Write a 16-bit big endian unsigned value to the specified 8-bit
        # address.
        with self._device as i2c:
            self._BUFFER[0] = address & 0xFF
            self._BUFFER[1] = (val >> 8) & 0xFF
            self._BUFFER[2] = val & 0xFF
            i2c.write(self._BUFFER, end=3)

    def _poll_reg1(self, mask):
        # Poll the CTRL REG1 value for the specified masked bits to NOT be
        # present.
        while self._read_u8(_MPL3115A2_CTRL_REG1) & mask > 0:
            time.sleep(0.01)

    @property
    def pressure(self):
        """Read the barometric pressure detected by the sensor in Pascals."""
        # First poll for a measurement to be finished.
        self._poll_reg1(_MPL3115A2_CTRL_REG1_OST)
        # Set control bits for pressure reading.
        self._ctrl_reg1 &= ~0b10000000  # Turn off bit 7, ALT.
        self._write_u8(_MPL3115A2_CTRL_REG1, self._ctrl_reg1)
        self._ctrl_reg1 |= 0b00000010  # Set OST to 1 to start measurement.
        self._write_u8(_MPL3115A2_CTRL_REG1, self._ctrl_reg1)
        # Poll status for PDR to be set.
        while (
            self._read_u8(_MPL3115A2_REGISTER_STATUS) & _MPL3115A2_REGISTER_STATUS_PDR
            == 0
        ):
            time.sleep(0.01)
        # Read 3 bytes of pressure data into buffer.
        self._read_into(_MPL3115A2_REGISTER_PRESSURE_MSB, self._BUFFER, count=3)
        # Reconstruct 20-bit pressure value.
        pressure = (
            (self._BUFFER[0] << 16) | (self._BUFFER[1] << 8) | self._BUFFER[2]
        ) & 0xFFFFFF
        pressure >>= 4
        # Scale down to pascals.
        return pressure / 4.0

    @property
    def altitude(self):
        """Read the altitude as calculated based on the sensor pressure and
        previously configured pressure at sea-level.  This will return a
        value in meters.  Set the sea-level pressure by updating the
        sealevel_pressure property first to get a more accurate altitude value.
        """
        # First poll for a measurement to be finished.
        self._poll_reg1(_MPL3115A2_CTRL_REG1_OST)
        # Set control bits for pressure reading.
        self._ctrl_reg1 |= 0b10000000  # Turn on bit 0, ALT.
        self._write_u8(_MPL3115A2_CTRL_REG1, self._ctrl_reg1)
        self._ctrl_reg1 |= 0b00000010  # Set OST to 1 to start measurement.
        self._write_u8(_MPL3115A2_CTRL_REG1, self._ctrl_reg1)
        # Poll status for PDR to be set.
        while (
            self._read_u8(_MPL3115A2_REGISTER_STATUS) & _MPL3115A2_REGISTER_STATUS_PDR
            == 0
        ):
            time.sleep(0.01)
        # Read 3 bytes of altitude data into buffer.
        # Yes even though this is the address of the pressure register it
        # returns altitude when the ALT bit is set above.
        self._read_into(_MPL3115A2_REGISTER_PRESSURE_MSB, self._BUFFER, count=3)
        # Reconstruct signed 32-bit altitude value (actually 24 bits shifted up
        # and then scaled down).
        self._BUFFER[3] = 0  # Top 3 bytes of buffer were read from the chip.
        altitude = struct.unpack(">i", self._BUFFER[0:4])[0]
        # Scale down to meters.
        return altitude / 65535.0

    @property
    def temperature(self):
        """Read the temperature as measured by the sensor in degrees Celsius."""
        # Poll status for TDR to be set.
        while (
            self._read_u8(_MPL3115A2_REGISTER_STATUS) & _MPL3115A2_REGISTER_STATUS_TDR
            == 0
        ):
            time.sleep(0.01)
        # Read 2 bytes of data from temp register.
        self._read_into(_MPL3115A2_REGISTER_TEMP_MSB, self._BUFFER, count=2)
        # Reconstruct signed 12-bit value.
        temperature = struct.unpack(">h", self._BUFFER[0:2])[0]
        temperature >>= 4
        # Scale down to degrees Celsius.
        return temperature / 16.0

    @property
    def sealevel_pressure(self):
        """Read and write the pressure at sea-level used to calculate altitude.
        You must look this up from a local weather or meteorlogical report for
        the best accuracy.  This is a value in Pascals.
        """
        # Read the sea level pressure in bars.
        self._read_into(_MPL3115A2_BAR_IN_MSB, self._BUFFER, count=2)
        # Reconstruct 16-bit value and scale back to pascals.
        pressure = (self._BUFFER[0] << 8) | self._BUFFER[1]
        return pressure * 2.0

    @sealevel_pressure.setter
    def sealevel_pressure(self, val):
        # Convert to bars of pressure and write to the sealevel register.
        bars = val // 2
        self._write_u16_be(_MPL3115A2_BAR_IN_MSB, bars)
