# SPDX-FileCopyrightText: 2019 Bryan Siepert for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_tc74`
================================================================================

CircuitPython library for the Microchip TC74 Digital Temperature Sensor

* Author(s): Bryan Siepert, Garrett Koller

Implementation Notes
--------------------

**Hardware:**

* Adafruit TC74: https://www.adafruit.com/product/4375

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://github.com/adafruit/circuitpython/releases
* Adafruit's Bus Device library: https://github.com/adafruit/Adafruit_CircuitPython_BusDevice
* Adafruit's Register library: https://github.com/adafruit/Adafruit_CircuitPython_Register
"""

from adafruit_register.i2c_struct import ROUnaryStruct
from adafruit_register.i2c_bit import RWBit, ROBit
import adafruit_bus_device.i2c_device as i2cdevice

__version__ = "1.0.2"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_TC74.git"
# pylint: disable=too-few-public-methods
TC74_DEFAULT_ADDRESS = 0x48

TC74_REGISTER_TEMP = 0  # Temperature register (read-only)
TC74_REGISTER_CONFIG = 1  # Configuration register
TC74_SHUTDOWN_BIT = 7  # Shutdown bit in Configuration register
TC74_DATA_READY_BIT = 6  # Data Ready bit in Configuration register
# pylint: enable=too-few-public-methods


class TC74:
    """
    Driver for the Microchip TC74 Digital Temperature Sensor.
    :param i2c_bus: The I2C bus the TC74 is connected to.
    :param address: The I2C device address for the sensor. Default is
    ``0x48``.
    """

    def __init__(self, i2c_bus, address=TC74_DEFAULT_ADDRESS):
        self.i2c_device = i2cdevice.I2CDevice(i2c_bus, address)

    _temperature = ROUnaryStruct(TC74_REGISTER_TEMP, "b")

    shutdown = RWBit(TC74_REGISTER_CONFIG, TC74_SHUTDOWN_BIT, lsb_first=True)
    """Set to True to turn off the temperature measurement circuitry in
    the sensor. While shut down the configurations properties can still
    be read or written but the temperature will not be measured."""

    data_ready = ROBit(TC74_REGISTER_CONFIG, TC74_DATA_READY_BIT, lsb_first=True)
    """Read-only bit that indicates when the temperature register is
    ready to be read from, especially after power-on or when switching
    from the shutdown to the normal state."""

    @property
    def temperature(self):
        """
        Returns the current temperature in degrees celsius. Resolution
        is 1 degrees C.
        """
        return self._temperature
