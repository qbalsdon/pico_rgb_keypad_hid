# SPDX-FileCopyrightText: 2019 Bryan Siepert for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_ds3502`
================================================================================

CircuitPython library for the Maxim DS3502 I2C Digital Potentionmeter


* Author(s): Bryan Siepert

Implementation Notes
--------------------

**Hardware:**

* `Adafruit DS3502 <https://www.adafruit.com/product/4286>`_

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://github.com/adafruit/circuitpython/releases



 * Adafruit's Bus Device library: https://github.com/adafruit/Adafruit_CircuitPython_BusDevice
 * Adafruit's Register library: https://github.com/adafruit/Adafruit_CircuitPython_Register
"""

# imports

__version__ = "1.1.6"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_DS3502.git"


from time import sleep
from micropython import const
from adafruit_register.i2c_struct import UnaryStruct
from adafruit_register.i2c_bit import RWBit
import adafruit_bus_device.i2c_device as i2cdevice

_REG_WIPER = const(0x00)  # Wiper value register (R/W)
_REG_CONTROL = const(0x02)  # Configuration Register (R/W)


class DS3502:
    """Driver for the DS3502 I2C Digital Potentiometer.

    :param ~busio.I2C i2c_bus: The I2C bus the DS3502 is connected to.
    :param address: The I2C device address for the sensor. Default is ``0x40``.
    """

    def __init__(self, i2c_bus, address=0x28):
        self.i2c_device = i2cdevice.I2CDevice(i2c_bus, address)

        # set to mode 1 on init to not write to the IVR every time you set
        self._write_only_to_wiper = True

    _wiper = UnaryStruct(_REG_WIPER, ">B")
    _write_only_to_wiper = RWBit(_REG_CONTROL, 7)

    @property
    def wiper(self):
        """The value of the potentionmeter's wiper.

        :param wiper_value: The value from 0-127 to set the wiper to.
        """
        return self._wiper

    @wiper.setter
    def wiper(self, value):
        if value < 0 or value > 127:
            raise ValueError("wiper must be from 0-127")
        self._wiper = value

    def set_default(self, default):
        """Sets the wiper's default value and current value to the given value

        :param new_default: The value from 0-127 to set as the wiper's default.
        """
        self._write_only_to_wiper = False
        self.wiper = default
        sleep(0.1)  # wait for write to eeprom to finish
        self._write_only_to_wiper = True
