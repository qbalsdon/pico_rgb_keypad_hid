# SPDX-FileCopyrightText: 2017 Scott Shawcroft for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_mcp9808` - MCP9808 I2C Temperature Sensor
====================================================

CircuitPython library to support MCP9808 high accuracy temperature sensor.

* Author(s): Scott Shawcroft

Implementation Notes
--------------------

**Hardware:**

* Adafruit `MCP9808 High Accuracy I2C Temperature Sensor Breakout
  <https://www.adafruit.com/products/1782>`_ (Product ID: 1782)

**Software and Dependencies:**

* Adafruit CircuitPython firmware (0.8.0+) for the ESP8622 and M0-based boards:
  https://github.com/adafruit/circuitpython/releases
* Adafruit's Bus Device library: https://github.com/adafruit/Adafruit_CircuitPython_BusDevice

**Notes:**

#.  Datasheet: http://www.adafruit.com/datasheets/MCP9808.pdf

"""

__version__ = "3.3.4"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_MCP9808.git"

from adafruit_bus_device.i2c_device import I2CDevice

# Resolution settings
HALF_C = 0x0
QUARTER_C = 0x1
EIGHTH_C = 0x2
SIXTEENTH_C = 0x3


class MCP9808:
    """Interface to the MCP9808 temperature sensor."""

    # alert_lower_temperature_bound
    # alert_upper_temperature_bound
    # critical_temperature
    # temperature
    # temperature_resolution

    def __init__(self, i2c_bus, address=0x18):
        self.i2c_device = I2CDevice(i2c_bus, address)

        # Verify the manufacturer and device ids to ensure we are talking to
        # what we expect.
        self.buf = bytearray(3)
        self.buf[0] = 0x06
        with self.i2c_device as i2c:
            i2c.write_then_readinto(self.buf, self.buf, out_end=1, in_start=1)

        ok = self.buf[2] == 0x54 and self.buf[1] == 0

        # Check device id.
        self.buf[0] = 0x07
        with self.i2c_device as i2c:
            i2c.write_then_readinto(self.buf, self.buf, out_end=1, in_start=1)

        if not ok or self.buf[1] != 0x04:
            raise ValueError(
                "Unable to find MCP9808 at i2c address " + str(hex(address))
            )

    @property
    def temperature(self):
        """Temperature in celsius. Read-only."""
        self.buf[0] = 0x05
        with self.i2c_device as i2c:
            i2c.write_then_readinto(self.buf, self.buf, out_end=1, in_start=1)

        # Clear flags from the value
        self.buf[1] = self.buf[1] & 0x1F
        if self.buf[1] & 0x10 == 0x10:
            self.buf[1] = self.buf[1] & 0x0F
            return (self.buf[1] * 16 + self.buf[2] / 16.0) - 256
        return self.buf[1] * 16 + self.buf[2] / 16.0
