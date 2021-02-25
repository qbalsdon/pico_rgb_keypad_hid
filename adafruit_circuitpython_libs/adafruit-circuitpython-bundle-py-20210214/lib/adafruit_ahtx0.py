# SPDX-FileCopyrightText: 2020 Kattni Rembor for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_ahtx0`
================================================================================

CircuitPython driver for the Adafruit AHT10 Humidity and Temperature Sensor


* Author(s): Kattni Rembor

Implementation Notes
--------------------

**Hardware:**

* This is a library for the Adafruit AHT20 breakout:
  https://www.adafruit.com/product/4566

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://github.com/adafruit/circuitpython/releases
* Adafruit's Bus Device library: https://github.com/adafruit/Adafruit_CircuitPython_BusDevice
"""

import time
from adafruit_bus_device.i2c_device import I2CDevice
from micropython import const

__version__ = "1.0.4"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_AHTx0.git"

AHTX0_I2CADDR_DEFAULT = const(0x38)  # Default I2C address
AHTX0_CMD_CALIBRATE = const(0xE1)  # Calibration command
AHTX0_CMD_TRIGGER = const(0xAC)  # Trigger reading command
AHTX0_CMD_SOFTRESET = const(0xBA)  # Soft reset command
AHTX0_STATUS_BUSY = const(0x80)  # Status bit for busy
AHTX0_STATUS_CALIBRATED = const(0x08)  # Status bit for calibrated


class AHTx0:
    """Interface library for AHT10/AHT20 temperature+humidity sensors"""

    def __init__(self, i2c_bus, address=AHTX0_I2CADDR_DEFAULT):
        time.sleep(0.02)  # 20ms delay to wake up
        self.i2c_device = I2CDevice(i2c_bus, address)
        self._buf = bytearray(6)
        self.reset()
        if not self.calibrate():
            raise RuntimeError("Could not calibrate")
        self._temp = None
        self._humidity = None

    def reset(self):
        """Perform a soft-reset of the AHT"""
        self._buf[0] = AHTX0_CMD_SOFTRESET
        with self.i2c_device as i2c:
            i2c.write(self._buf, start=0, end=1)
        time.sleep(0.02)  # 20ms delay to wake up

    def calibrate(self):
        """Ask the sensor to self-calibrate. Returns True on success, False otherwise"""
        self._buf[0] = AHTX0_CMD_CALIBRATE
        self._buf[1] = 0x08
        self._buf[2] = 0x00
        with self.i2c_device as i2c:
            i2c.write(self._buf, start=0, end=3)
        while self.status & AHTX0_STATUS_BUSY:
            time.sleep(0.01)
        if not self.status & AHTX0_STATUS_CALIBRATED:
            return False
        return True

    @property
    def status(self):
        """The status byte initially returned from the sensor, see datasheet for details"""
        with self.i2c_device as i2c:
            i2c.readinto(self._buf, start=0, end=1)
        # print("status: "+hex(self._buf[0]))
        return self._buf[0]

    @property
    def relative_humidity(self):
        """The measured relative humidity in percent."""
        self._readdata()
        return self._humidity

    @property
    def temperature(self):
        """The measured temperature in degrees Celcius."""
        self._readdata()
        return self._temp

    def _readdata(self):
        """Internal function for triggering the AHT to read temp/humidity"""
        self._buf[0] = AHTX0_CMD_TRIGGER
        self._buf[1] = 0x33
        self._buf[2] = 0x00
        with self.i2c_device as i2c:
            i2c.write(self._buf, start=0, end=3)
        while self.status & AHTX0_STATUS_BUSY:
            time.sleep(0.01)
        with self.i2c_device as i2c:
            i2c.readinto(self._buf, start=0, end=6)

        self._humidity = (
            (self._buf[1] << 12) | (self._buf[2] << 4) | (self._buf[3] >> 4)
        )
        self._humidity = (self._humidity * 100) / 0x100000
        self._temp = ((self._buf[3] & 0xF) << 16) | (self._buf[4] << 8) | self._buf[5]
        self._temp = ((self._temp * 200.0) / 0x100000) - 50
