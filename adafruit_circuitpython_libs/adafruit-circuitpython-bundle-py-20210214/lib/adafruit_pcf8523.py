# SPDX-FileCopyrightText: 2016 Philip R. Moyer for Adafruit Industries
# SPDX-FileCopyrightText: 2016 Radomir Dopieralski for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_pcf8523` - PCF8523 Real Time Clock module
====================================================

This library supports the use of the PCF8523-based RTC in CircuitPython. It
contains a base RTC class used by all Adafruit RTC libraries. This base
class is inherited by the chip-specific subclasses.

Functions are included for reading and writing registers and manipulating
datetime objects.

Author(s): Philip R. Moyer and Radomir Dopieralski for Adafruit Industries.
Date: November 2016
Affiliation: Adafruit Industries

Implementation Notes
--------------------

**Hardware:**

* Adafruit `Adalogger FeatherWing - RTC + SD Add-on <https://www.adafruit.com/products/2922>`_
  (Product ID: 2922)
* Adafruit `PCF8523 RTC breakout <https://www.adafruit.com/products/3295>`_ (Product ID: 3295)

**Software and Dependencies:**

* Adafruit CircuitPython firmware: https://github.com/adafruit/circuitpython/releases
* Adafruit's Register library: https://github.com/adafruit/Adafruit_CircuitPython_Register
* Adafruit's Bus Device library: https://github.com/adafruit/Adafruit_CircuitPython_BusDevice

**Notes:**

#. Milliseconds are not supported by this RTC.
#. Datasheet: http://cache.nxp.com/documents/data_sheet/PCF8523.pdf

"""

__version__ = "1.5.3"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_PCF8523.git"

from adafruit_bus_device.i2c_device import I2CDevice
from adafruit_register import i2c_bit
from adafruit_register import i2c_bits
from adafruit_register import i2c_bcd_alarm
from adafruit_register import i2c_bcd_datetime

STANDARD_BATTERY_SWITCHOVER_AND_DETECTION = 0b000
BATTERY_SWITCHOVER_OFF = 0b111


class PCF8523:
    """Interface to the PCF8523 RTC."""

    lost_power = i2c_bit.RWBit(0x03, 7)
    """True if the device has lost power since the time was set."""

    power_management = i2c_bits.RWBits(3, 0x02, 5)
    """Power management state that dictates battery switchover, power sources
    and low battery detection. Defaults to BATTERY_SWITCHOVER_OFF (0b000)."""

    # The False means that day comes before weekday in the registers. The 0 is
    # that the first day of the week is value 0 and not 1.
    datetime_register = i2c_bcd_datetime.BCDDateTimeRegister(0x03, False, 0)
    """Current date and time."""

    # The False means that day and weekday share a register. The 0 is that the
    # first day of the week is value 0 and not 1.
    alarm = i2c_bcd_alarm.BCDAlarmTimeRegister(
        0x0A, has_seconds=False, weekday_shared=False, weekday_start=0
    )
    """Alarm time for the first alarm."""

    alarm_interrupt = i2c_bit.RWBit(0x00, 1)
    """True if the interrupt pin will output when alarm is alarming."""

    alarm_status = i2c_bit.RWBit(0x01, 3)
    """True if alarm is alarming. Set to False to reset."""

    battery_low = i2c_bit.ROBit(0x02, 2)
    """True if the battery is low and should be replaced."""

    high_capacitance = i2c_bit.RWBit(0x00, 7)
    """True for high oscillator capacitance (12.5pF), otherwise lower (7pF)"""

    calibration_schedule_per_minute = i2c_bit.RWBit(0x0E, 7)
    """False to apply the calibration offset every 2 hours (1 LSB = 4.340ppm);
    True to offset every minute (1 LSB = 4.069ppm).  The default, False,
    consumes less power.  See datasheet figures 28-31 for details."""

    calibration = i2c_bits.RWBits(  # pylint: disable=unexpected-keyword-arg
        7, 0xE, 0, signed=True
    )
    """Calibration offset to apply, from -64 to +63.  See the PCF8523 datasheet
    figure 18 for the offset calibration calculation workflow."""

    def __init__(self, i2c_bus):
        self.i2c_device = I2CDevice(i2c_bus, 0x68)

        # Try and verify this is the RTC we expect by checking the timer B
        # frequency control bits which are 1 on reset and shouldn't ever be
        # changed.
        buf = bytearray(2)
        buf[0] = 0x12
        with self.i2c_device as i2c:
            i2c.write_then_readinto(buf, buf, out_end=1, in_start=1)

        if (buf[1] & 0b00000111) != 0b00000111:
            raise ValueError("Unable to find PCF8523 at i2c address 0x68.")

    @property
    def datetime(self):
        """Gets the current date and time or sets the current date and time then starts the
        clock."""
        return self.datetime_register

    @datetime.setter
    def datetime(self, value):
        # Automatically sets lost_power to false.
        self.power_management = STANDARD_BATTERY_SWITCHOVER_AND_DETECTION
        self.datetime_register = value
