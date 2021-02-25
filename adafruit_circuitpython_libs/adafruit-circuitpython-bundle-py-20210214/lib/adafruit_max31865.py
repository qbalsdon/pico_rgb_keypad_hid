# SPDX-FileCopyrightText: 2017 Tony DiCola for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_max31865`
====================================================

CircuitPython module for the MAX31865 platinum RTD temperature sensor.  See
examples/simpletest.py for an example of the usage.

* Author(s): Tony DiCola

Implementation Notes
--------------------

**Hardware:**

* Adafruit `Universal Thermocouple Amplifier MAX31856 Breakout
  <https://www.adafruit.com/product/3263>`_ (Product ID: 3263)

* Adafruit `PT100 RTD Temperature Sensor Amplifier - MAX31865
  <https://www.adafruit.com/product/3328>`_ (Product ID: 3328)

* Adafruit `PT1000 RTD Temperature Sensor Amplifier - MAX31865
  <https://www.adafruit.com/product/3648>`_ (Product ID: 3648)

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the ESP8622 and M0-based boards:
  https://github.com/adafruit/circuitpython/releases
* Adafruit's Bus Device library: https://github.com/adafruit/Adafruit_CircuitPython_BusDevice
"""
import math
import time

from micropython import const

import adafruit_bus_device.spi_device as spi_device

__version__ = "2.2.7"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_MAX31865.git"

# Register and other constant values:
_MAX31865_CONFIG_REG = const(0x00)
_MAX31865_CONFIG_BIAS = const(0x80)
_MAX31865_CONFIG_MODEAUTO = const(0x40)
_MAX31865_CONFIG_MODEOFF = const(0x00)
_MAX31865_CONFIG_1SHOT = const(0x20)
_MAX31865_CONFIG_3WIRE = const(0x10)
_MAX31865_CONFIG_24WIRE = const(0x00)
_MAX31865_CONFIG_FAULTSTAT = const(0x02)
_MAX31865_CONFIG_FILT50HZ = const(0x01)
_MAX31865_CONFIG_FILT60HZ = const(0x00)
_MAX31865_RTDMSB_REG = const(0x01)
_MAX31865_RTDLSB_REG = const(0x02)
_MAX31865_HFAULTMSB_REG = const(0x03)
_MAX31865_HFAULTLSB_REG = const(0x04)
_MAX31865_LFAULTMSB_REG = const(0x05)
_MAX31865_LFAULTLSB_REG = const(0x06)
_MAX31865_FAULTSTAT_REG = const(0x07)
_MAX31865_FAULT_HIGHTHRESH = const(0x80)
_MAX31865_FAULT_LOWTHRESH = const(0x40)
_MAX31865_FAULT_REFINLOW = const(0x20)
_MAX31865_FAULT_REFINHIGH = const(0x10)
_MAX31865_FAULT_RTDINLOW = const(0x08)
_MAX31865_FAULT_OVUV = const(0x04)
_RTD_A = 3.9083e-3
_RTD_B = -5.775e-7


class MAX31865:
    """Driver for the MAX31865 thermocouple amplifier."""

    # Class-level buffer for reading and writing data with the sensor.
    # This reduces memory allocations but means the code is not re-entrant or
    # thread safe!
    _BUFFER = bytearray(3)

    def __init__(
        self,
        spi,
        cs,
        *,
        rtd_nominal=100,
        ref_resistor=430.0,
        wires=2,
        filter_frequency=60
    ):
        self.rtd_nominal = rtd_nominal
        self.ref_resistor = ref_resistor
        self._device = spi_device.SPIDevice(
            spi, cs, baudrate=500000, polarity=0, phase=1
        )
        # Set 50Hz or 60Hz filter.
        if filter_frequency not in (50, 60):
            raise ValueError("Filter_frequency must be a value of 50 or 60!")
        config = self._read_u8(_MAX31865_CONFIG_REG)
        if filter_frequency == 50:
            config |= _MAX31865_CONFIG_FILT50HZ
        else:
            config &= ~_MAX31865_CONFIG_FILT50HZ

        # Set wire config register based on the number of wires specified.
        if wires not in (2, 3, 4):
            raise ValueError("Wires must be a value of 2, 3, or 4!")
        if wires == 3:
            config |= _MAX31865_CONFIG_3WIRE
        else:
            # 2 or 4 wire
            config &= ~_MAX31865_CONFIG_3WIRE
        self._write_u8(_MAX31865_CONFIG_REG, config)
        # Default to no bias and no auto conversion.
        self.bias = False
        self.auto_convert = False

    # pylint: disable=no-member
    def _read_u8(self, address):
        # Read an 8-bit unsigned value from the specified 8-bit address.
        with self._device as device:
            self._BUFFER[0] = address & 0x7F
            device.write(self._BUFFER, end=1)
            device.readinto(self._BUFFER, end=1)
        return self._BUFFER[0]

    def _read_u16(self, address):
        # Read a 16-bit BE unsigned value from the specified 8-bit address.
        with self._device as device:
            self._BUFFER[0] = address & 0x7F
            device.write(self._BUFFER, end=1)
            device.readinto(self._BUFFER, end=2)
        return (self._BUFFER[0] << 8) | self._BUFFER[1]

    def _write_u8(self, address, val):
        # Write an 8-bit unsigned value to the specified 8-bit address.
        with self._device as device:
            self._BUFFER[0] = (address | 0x80) & 0xFF
            self._BUFFER[1] = val & 0xFF
            device.write(self._BUFFER, end=2)

    # pylint: enable=no-member

    @property
    def bias(self):
        """The state of the sensor's bias (True/False)."""
        return bool(self._read_u8(_MAX31865_CONFIG_REG) & _MAX31865_CONFIG_BIAS)

    @bias.setter
    def bias(self, val):
        config = self._read_u8(_MAX31865_CONFIG_REG)
        if val:
            config |= _MAX31865_CONFIG_BIAS  # Enable bias.
        else:
            config &= ~_MAX31865_CONFIG_BIAS  # Disable bias.
        self._write_u8(_MAX31865_CONFIG_REG, config)

    @property
    def auto_convert(self):
        """The state of the sensor's automatic conversion
        mode (True/False).
        """
        return bool(self._read_u8(_MAX31865_CONFIG_REG) & _MAX31865_CONFIG_MODEAUTO)

    @auto_convert.setter
    def auto_convert(self, val):
        config = self._read_u8(_MAX31865_CONFIG_REG)
        if val:
            config |= _MAX31865_CONFIG_MODEAUTO  # Enable auto convert.
        else:
            config &= ~_MAX31865_CONFIG_MODEAUTO  # Disable auto convert.
        self._write_u8(_MAX31865_CONFIG_REG, config)

    @property
    def fault(self):
        """The fault state of the sensor.  Use ``clear_faults()`` to clear the
        fault state.  Returns a 6-tuple of boolean values which indicate if any
        faults are present:

        - HIGHTHRESH
        - LOWTHRESH
        - REFINLOW
        - REFINHIGH
        - RTDINLOW
        - OVUV
        """
        faults = self._read_u8(_MAX31865_FAULTSTAT_REG)
        highthresh = bool(faults & _MAX31865_FAULT_HIGHTHRESH)
        lowthresh = bool(faults & _MAX31865_FAULT_LOWTHRESH)
        refinlow = bool(faults & _MAX31865_FAULT_REFINLOW)
        refinhigh = bool(faults & _MAX31865_FAULT_REFINHIGH)
        rtdinlow = bool(faults & _MAX31865_FAULT_RTDINLOW)
        ovuv = bool(faults & _MAX31865_FAULT_OVUV)
        return (highthresh, lowthresh, refinlow, refinhigh, rtdinlow, ovuv)

    def clear_faults(self):
        """Clear any fault state previously detected by the sensor."""
        config = self._read_u8(_MAX31865_CONFIG_REG)
        config &= ~0x2C
        config |= _MAX31865_CONFIG_FAULTSTAT
        self._write_u8(_MAX31865_CONFIG_REG, config)

    def read_rtd(self):
        """Perform a raw reading of the thermocouple and return its 15-bit
        value.  You'll need to manually convert this to temperature using the
        nominal value of the resistance-to-digital conversion and some math.  If you just want
        temperature use the temperature property instead.
        """
        self.clear_faults()
        self.bias = True
        time.sleep(0.01)
        config = self._read_u8(_MAX31865_CONFIG_REG)
        config |= _MAX31865_CONFIG_1SHOT
        self._write_u8(_MAX31865_CONFIG_REG, config)
        time.sleep(0.065)
        rtd = self._read_u16(_MAX31865_RTDMSB_REG)
        self.bias = False
        # Remove fault bit.
        rtd >>= 1
        return rtd

    @property
    def resistance(self):
        """Read the resistance of the RTD and return its value in Ohms."""
        resistance = self.read_rtd()
        resistance /= 32768
        resistance *= self.ref_resistor
        return resistance

    @property
    def temperature(self):
        """Read the temperature of the sensor and return its value in degrees
        Celsius.
        """
        # This math originates from:
        # http://www.analog.com/media/en/technical-documentation/application-notes/AN709_0.pdf
        # To match the naming from the app note we tell lint to ignore the Z1-4
        # naming.
        # pylint: disable=invalid-name
        raw_reading = self.resistance
        Z1 = -_RTD_A
        Z2 = _RTD_A * _RTD_A - (4 * _RTD_B)
        Z3 = (4 * _RTD_B) / self.rtd_nominal
        Z4 = 2 * _RTD_B
        temp = Z2 + (Z3 * raw_reading)
        temp = (math.sqrt(temp) + Z1) / Z4
        if temp >= 0:
            return temp

        # For the following math to work, nominal RTD resistance must be normalized to 100 ohms
        raw_reading /= self.rtd_nominal
        raw_reading *= 100

        rpoly = raw_reading
        temp = -242.02
        temp += 2.2228 * rpoly
        rpoly *= raw_reading  # square
        temp += 2.5859e-3 * rpoly
        rpoly *= raw_reading  # ^3
        temp -= 4.8260e-6 * rpoly
        rpoly *= raw_reading  # ^4
        temp -= 2.8183e-8 * rpoly
        rpoly *= raw_reading  # ^5
        temp += 1.5243e-10 * rpoly
        return temp
