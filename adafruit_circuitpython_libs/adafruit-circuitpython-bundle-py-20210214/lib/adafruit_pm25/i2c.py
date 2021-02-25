# SPDX-FileCopyrightText: 2020 ladyada for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_pm25.i2c`
================================================================================

I2C module for CircuitPython library for PM2.5 Air Quality Sensors


* Author(s): ladyada

Implementation Notes
--------------------

**Hardware:**

Works with most (any?) Plantower I2C interfaced PM2.5 sensor.

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://github.com/adafruit/circuitpython/releases
* Adafruit's Bus Device library: https://github.com/adafruit/Adafruit_CircuitPython_BusDevice

"""

# imports
import time
from digitalio import Direction
from adafruit_bus_device.i2c_device import I2CDevice
from . import PM25


class PM25_I2C(PM25):
    """
    A module for using the PM2.5 Air quality sensor over I2C
    """

    def __init__(self, i2c_bus, reset_pin=None, address=0x12):
        if reset_pin:
            # Reset device
            reset_pin.direction = Direction.OUTPUT
            reset_pin.value = False
            time.sleep(0.01)
            reset_pin.value = True
            # it takes at least a second to start up
            time.sleep(1)

        for _ in range(5):  # try a few times, it can be sluggish
            try:
                self.i2c_device = I2CDevice(i2c_bus, address)
                break
            except ValueError:
                time.sleep(1)
                continue
        else:
            raise RuntimeError("Unable to find PM2.5 device")
        super().__init__()

    def _read_into_buffer(self):
        with self.i2c_device as i2c:
            try:
                i2c.readinto(self._buffer)
            except OSError as err:
                raise RuntimeError("Unable to read from PM2.5 over I2C") from err
