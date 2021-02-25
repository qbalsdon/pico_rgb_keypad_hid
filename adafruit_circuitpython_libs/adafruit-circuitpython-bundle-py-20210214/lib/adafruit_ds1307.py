# SPDX-FileCopyrightText: 2016 Philip R. Moyer for Adafruit Industries
# SPDX-FileCopyrightText: 2016 Radomir Dopieralski for Adafruit Industries
#
# SPDX-License-Identifier: MIT

# pylint: disable=too-few-public-methods

"""
`adafruit_ds1307` - DS1307 Real Time Clock module
=================================================

CircuitPython library to support DS1307 Real Time Clock (RTC).

This library supports the use of the DS1307-based RTC in CircuitPython.

Beware that most CircuitPython compatible hardware are 3.3v logic level! Make
sure that the input pin is 5v tolerant.

* Author(s): Philip R. Moyer and Radomir Dopieralski for Adafruit Industries

Implementation Notes
--------------------

**Hardware:**

* Adafruit `DS1307 RTC breakout <https://www.adafruit.com/products/3296>`_ (Product ID: 3296)

**Software and Dependencies:**

* Adafruit CircuitPython firmware (0.8.0+) for the ESP8622 and M0-based boards:
    https://github.com/adafruit/circuitpython/releases
* Adafruit's Register library: https://github.com/adafruit/Adafruit_CircuitPython_Register
* Adafruit's Bus Device library: https://github.com/adafruit/Adafruit_CircuitPython_BusDevice

**Notes:**

#.  Milliseconds are not supported by this RTC.
#.  Alarms and timers are not supported by this RTC.
#.  Datasheet: https://datasheets.maximintegrated.com/en/ds/DS1307.pdf

"""

from adafruit_bus_device.i2c_device import I2CDevice
from adafruit_register import i2c_bit
from adafruit_register import i2c_bcd_datetime

__version__ = "2.1.5"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_DS1307.git"


class DS1307:
    """Interface to the DS1307 RTC."""

    disable_oscillator = i2c_bit.RWBit(0x0, 7)
    """True if the oscillator is disabled."""

    datetime_register = i2c_bcd_datetime.BCDDateTimeRegister(0x00)
    """Current date and time."""

    def __init__(self, i2c_bus):
        self.i2c_device = I2CDevice(i2c_bus, 0x68)

        # Try and verify this is the RTC we expect by checking the rate select
        # control bits which are 1 on reset and shouldn't ever be changed.
        buf = bytearray(2)
        buf[0] = 0x07
        with self.i2c_device as i2c:
            i2c.write_then_readinto(buf, buf, out_end=1, in_start=1)

        if (buf[1] & 0b00000011) != 0b00000011:
            raise ValueError("Unable to find DS1307 at i2c address 0x68.")

    @property
    def datetime(self):
        """Gets the current date and time or sets the current date and time then starts the
        clock."""
        return self.datetime_register

    @datetime.setter
    def datetime(self, value):
        self.disable_oscillator = False
        self.datetime_register = value
