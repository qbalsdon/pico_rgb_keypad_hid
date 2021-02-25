# The MIT License (MIT)
#
# Copyright (c) 2020 Bryan Siepert for Adafruit Industries
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
"""
`adafruit_ds1841`
================================================================================

Library for the DS1841 I2C Logarithmic Resistor

* Author(s): Bryan Siepert

Implementation Notes
--------------------

**Hardware:**

* Adafruit's DS1841 Breakout: https://www.adafruit.com/product/4570

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://circuitpython.org/downloads
* Adafruit's Bus Device library: https://github.com/adafruit/Adafruit_CircuitPython_BusDevice
* Adafruit's Register library: https://github.com/adafruit/Adafruit_CircuitPython_Register"""

__version__ = "1.0.3"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_DS1841.git"

from time import sleep
import adafruit_bus_device.i2c_device as i2c_device
from adafruit_register.i2c_struct import UnaryStruct
from adafruit_register.i2c_struct_array import StructArray
from adafruit_register.i2c_bit import RWBit


_DS1841_IVR = 0x00
_DS1841_CR0 = 0x02
_DS1841_CR1 = 0x03
_DS1841_LUTAR = 0x08
_DS1841_WR = 0x09
_DS1841_CR2 = 0x0A
_DS1841_TEMP = 0x0C
_DS1841_VOLTAGE = 0x0E
_DS1841_LUT = 0x80  # to C7h

_DS1841_VCC_LSB = 25.6
_DS1841_DEFAULT_ADDRESS = 0x28  # up to 0x2B


class DS1841:
    """Driver for the DS3502 I2C Digital Potentiometer.
    :param ~busio.I2C i2c_bus: The I2C bus the DS3502 is connected to.
    :param address: The I2C device address for the sensor. Default is ``0x28``.
    """

    _lut_address = UnaryStruct(_DS1841_LUTAR, ">B")
    _wiper_register = UnaryStruct(_DS1841_WR, ">B")

    _temperature_register = UnaryStruct(_DS1841_TEMP, ">b")
    _voltage_register = UnaryStruct(_DS1841_VOLTAGE, ">B")

    # NV-capable settings
    _disable_save_to_eeprom = RWBit(_DS1841_CR0, 7)
    # Can be shadowed by EEPROM
    _initial_value_register = UnaryStruct(_DS1841_IVR, ">B")
    _adder_mode_bit = RWBit(_DS1841_CR1, 1)
    _update_mode = RWBit(_DS1841_CR1, 0)

    _manual_lut_address = RWBit(_DS1841_CR2, 1)
    _manual_wiper_value = RWBit(_DS1841_CR2, 2)

    _lut = StructArray(_DS1841_LUT, ">B", 72)

    def __init__(self, i2c_bus, address=_DS1841_DEFAULT_ADDRESS):
        self.i2c_device = i2c_device.I2CDevice(i2c_bus, address)

        self._disable_save_to_eeprom = True  # turn off eeprom updates to IV and CR0
        self._adder_mode_bit = False  # Don't add IV to WR
        # UPDATE MODE MUST BE FALSE FOR WIPER TO SHADOW IV

        self._manual_lut_address = True  #
        self._manual_wiper_value = True  # update WR by I2C
        self._lut_mode_enabled = False
        self._update_mode = True

    @property
    def wiper(self):
        """The value of the potentionmeter's wiper.
            :param wiper_value: The value from 0-127 to set the wiper to.
        """
        return self._wiper_register

    @wiper.setter
    def wiper(self, value):
        if value > 127:
            raise AttributeError("wiper must be from 0-127")
        self._wiper_register = value

    @property
    def wiper_default(self):
        """Sets the wiper's default value and current value to the given value
            :param new_default: The value from 0-127 to set as the wiper's default.
        """

        return self._initial_value_register

    @wiper_default.setter
    def wiper_default(self, value):
        if value > 127:
            raise AttributeError("initial_value must be from 0-127")
        self._disable_save_to_eeprom = False
        # allows for IV to pass through to WR.
        # this setting is also saved to EEPROM so IV will load into WR on boot
        self._update_mode = False
        sleep(0.2)
        self._initial_value_register = value
        sleep(0.2)
        self._disable_save_to_eeprom = True
        # Turn update mode back on so temp and voltage update
        # and LUT usage works
        self._update_mode = True

    @property
    def temperature(self):
        """The current temperature in degrees celcius"""
        return self._temperature_register

    @property
    def voltage(self):
        """The current voltage between VCC and GND"""
        return self._voltage_register * _DS1841_VCC_LSB

    ######## LUTS on LUTS on LUTS
    @property
    def lut_mode_enabled(self):
        """Enables LUT mode. LUT mode takes sets the value of the Wiper based on the entry in a
        72-entry Look Up Table. The LUT entry is selected using the `lut_selection`
        property to set an index from 0-71
        """
        return self._lut_mode_enabled

    @lut_mode_enabled.setter
    def lut_mode_enabled(self, value):
        self._manual_lut_address = value
        self._update_mode = True
        self._manual_wiper_value = not value
        self._lut_mode_enabled = value

    def set_lut(self, index, value):
        """Set the value of an entry in the Look Up Table.
            :param index: The index of the entry to set, from 0-71.
            :param value: The value to set at the given index. The `wiper` will be set to this
            value when the LUT entry is selected using `lut_selection`
        """
        if value > 127:
            raise IndexError("set_lut value must be from 0-127")
        lut_value_byte = bytearray([value])
        self._lut[index] = lut_value_byte
        sleep(0.020)

    @property
    def lut_selection(self):
        """Choose the entry in the Look Up Table to use to set the wiper.
            :param index: The index of the entry to use, from 0-71.
        """
        if not self._lut_mode_enabled:
            raise RuntimeError(
                "lut_mode_enabled must be equal to True to use lut_selection"
            )
        return self._lut_address - _DS1841_LUT

    @lut_selection.setter
    def lut_selection(self, value):
        if value > 71 or value < 0:
            raise IndexError("lut_selection value must be from 0-71")
        self._lut_address = value + _DS1841_LUT
        sleep(0.020)
