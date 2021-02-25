# SPDX-FileCopyrightText: 2017 Tony DiCola for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_vcnl4010`
====================================================

CircuitPython module for the VCNL4010 proximity and light sensor.  See
examples/vcnl4010_simpletest.py for an example of the usage.

* Author(s): Tony DiCola

Implementation Notes
--------------------

**Hardware:**

* Adafruit `VCNL4010 Proximity/Light sensor breakout
  <https://www.adafruit.com/product/466>`_ (Product ID: 466)

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the ESP8622 and M0-based boards:
  https://github.com/adafruit/circuitpython/releases
* Adafruit's Bus Device library: https://github.com/adafruit/Adafruit_CircuitPython_BusDevice
"""
from micropython import const

import adafruit_bus_device.i2c_device as i2c_device


__version__ = "0.10.6"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_VCNL4010.git"


# Internal constants:
_VCNL4010_I2CADDR_DEFAULT = const(0x13)
_VCNL4010_COMMAND = const(0x80)
_VCNL4010_PRODUCTID = const(0x81)
_VCNL4010_PROXRATE = const(0x82)
_VCNL4010_IRLED = const(0x83)
_VCNL4010_AMBIENTPARAMETER = const(0x84)
_VCNL4010_AMBIENTDATA = const(0x85)
_VCNL4010_PROXIMITYDATA = const(0x87)
_VCNL4010_INTCONTROL = const(0x89)
_VCNL4010_PROXIMITYADJUST = const(0x8A)
_VCNL4010_INTSTAT = const(0x8E)
_VCNL4010_MODTIMING = const(0x8F)
_VCNL4010_MEASUREAMBIENT = const(0x10)
_VCNL4010_MEASUREPROXIMITY = const(0x08)
_VCNL4010_AMBIENTREADY = const(0x40)
_VCNL4010_PROXIMITYREADY = const(0x20)
_VCNL4010_AMBIENT_LUX_SCALE = 0.25  # Lux value per 16-bit result value.

# User-facing constants:
FREQUENCY_3M125 = 3
FREQUENCY_1M5625 = 2
FREQUENCY_781K25 = 1
FREQUENCY_390K625 = 0

# Disable pylint's name warning as it causes too much noise.  Suffixes like
# BE (big-endian) or mA (milli-amps) don't confirm to its conventions--by
# design (clarity of code and explicit units).  Disable this globally to prevent
# littering the code with pylint disable and enable and making it less readable.
# pylint: disable=invalid-name


class VCNL4010:
    """Vishay VCNL4010 proximity and ambient light sensor."""

    # Class-level buffer for reading and writing data with the sensor.
    # This reduces memory allocations but means the code is not re-entrant or
    # thread safe!
    _BUFFER = bytearray(3)

    def __init__(self, i2c, address=_VCNL4010_I2CADDR_DEFAULT):
        self._device = i2c_device.I2CDevice(i2c, address)
        # Verify chip ID.
        revision = self._read_u8(_VCNL4010_PRODUCTID)
        if (revision & 0xF0) != 0x20:
            raise RuntimeError("Failed to find VCNL4010, check wiring!")
        self.led_current = 20
        self.frequency = FREQUENCY_390K625
        self._write_u8(_VCNL4010_INTCONTROL, 0x08)

    def _read_u8(self, address):
        # Read an 8-bit unsigned value from the specified 8-bit address.
        with self._device as i2c:
            self._BUFFER[0] = address & 0xFF
            i2c.write_then_readinto(self._BUFFER, self._BUFFER, out_end=1, in_start=1)
        return self._BUFFER[1]

    def _read_u16BE(self, address):
        # Read a 16-bit big-endian unsigned value from the specified 8-bit address.
        with self._device as i2c:
            self._BUFFER[0] = address & 0xFF
            i2c.write_then_readinto(self._BUFFER, self._BUFFER, out_end=1, in_start=1)
        return (self._BUFFER[1] << 8) | self._BUFFER[2]

    def _write_u8(self, address, val):
        # Write an 8-bit unsigned value to the specified 8-bit address.
        with self._device as i2c:
            self._BUFFER[0] = address & 0xFF
            self._BUFFER[1] = val & 0xFF
            i2c.write(self._BUFFER, end=2)

    @property
    def led_current(self):
        """The current of the LED.  The value is in units of 10mA
        and can only be set to 0 (0mA/off) to 20 (200mA).  See the datasheet
        for how LED current impacts proximity measurements.  The default is
        200mA.
        """
        return self._read_u8(_VCNL4010_IRLED) & 0x3F

    @led_current.setter
    def led_current(self, val):
        assert 0 <= val <= 20
        self._write_u8(_VCNL4010_IRLED, val)

    @property
    def led_current_mA(self):
        """The current of the LED in milli-amps.  The value here is
        specified in a milliamps from 0-200.  Note that this value will be
        quantized down to a smaller less-accurate value as the chip only
        supports current changes in 10mA increments, i.e. a value of 123 mA will
        actually use 120 mA.  See the datasheet for how the LED current impacts
        proximity measurements, and the led_current property to explicitly set
        values without quanitization or unit conversion.
        """
        return self.led_current * 10

    @led_current_mA.setter
    def led_current_mA(self, val):
        self.led_current = val // 10

    @property
    def frequency(self):
        """
        The frequency of proximity measurements.  Must be a value of:

        - FREQUENCY_3M125: 3.125 Mhz
        - FREQUENCY_1M5625: 1.5625 Mhz
        - FREQUENCY_781K25: 781.25 Khz
        - FREQUENCY_390K625: 390.625 Khz (default)

        See the datasheet for how frequency changes the proximity detection
        accuracy.
        """
        return (self._read_u8(_VCNL4010_MODTIMING) >> 3) & 0x03

    @frequency.setter
    def frequency(self, val):
        assert 0 <= val <= 3
        timing = self._read_u8(_VCNL4010_MODTIMING)
        timing &= ~0b00011000
        timing |= (val << 3) & 0xFF
        self._write_u8(_VCNL4010_MODTIMING, timing)

    # Pylint gets confused with loops and return values.  Disable the spurious
    # warning for the next few functions (it hates when a loop returns a value).
    # pylint: disable=inconsistent-return-statements
    @property
    def proximity(self):
        """The detected proximity of an object in front of the sensor.  This
        is a unit-less unsigned 16-bit value (0-65535) INVERSELY proportional
        to the distance of an object in front of the sensor (up to a max of
        ~200mm).  For example a value of 10 is an object farther away than a
        value of 1000.  Note there is no conversion from this value to absolute
        distance possible, you can only make relative comparisons.
        """
        # Clear interrupt.
        status = self._read_u8(_VCNL4010_INTSTAT)
        status &= ~0x80
        self._write_u8(_VCNL4010_INTSTAT, status)
        # Grab a proximity measurement.
        self._write_u8(_VCNL4010_COMMAND, _VCNL4010_MEASUREPROXIMITY)
        # Wait for result, then read and return the 16-bit value.
        while True:
            result = self._read_u8(_VCNL4010_COMMAND)
            if result & _VCNL4010_PROXIMITYREADY:
                return self._read_u16BE(_VCNL4010_PROXIMITYDATA)

    @property
    def ambient(self):
        """The detected ambient light in front of the sensor.  This is
        a unit-less unsigned 16-bit value (0-65535) with higher values for
        more detected light.  See the ambient_lux property for a value in lux.
        """
        # Clear interrupt.
        status = self._read_u8(_VCNL4010_INTSTAT)
        status &= ~0x80
        self._write_u8(_VCNL4010_INTSTAT, status)
        # Grab an ambient light measurement.
        self._write_u8(_VCNL4010_COMMAND, _VCNL4010_MEASUREAMBIENT)
        # Wait for result, then read and return the 16-bit value.
        while True:
            result = self._read_u8(_VCNL4010_COMMAND)
            if result & _VCNL4010_AMBIENTREADY:
                return self._read_u16BE(_VCNL4010_AMBIENTDATA)

    # pylint: enable=inconsistent-return-statements

    @property
    def ambient_lux(self):
        """The detected ambient light in front of the sensor as a value in
        lux.
        """
        return self.ambient * _VCNL4010_AMBIENT_LUX_SCALE
