# SPDX-FileCopyrightText: 2018 Mikey Sklar for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_mlx90614`
====================================================

CircuitPython module for the MLX90614 IR object temperature sensor.

* Author(s): Mikey Sklar based on code from these projects:
  Limor Fried - https://github.com/adafruit/Adafruit-MLX90614-Library
  Bill Simpson - https://github.com/BillSimpson/ada_mlx90614
  Mike Causer - https://github.com/mcauser/micropython-mlx90614

Implementation Notes
--------------------

**Hardware:**

* Adafruit `Melexis Contact-less Infrared Sensor - MLX90614 3V
  <https://www.adafruit.com/product/1747>`_ (Product ID: 1747)

* Adafruit `Melexis Contact-less Infrared Sensor - MLX90614 5V
  <https://www.adafruit.com/product/1748>`_ (Product ID: 1748)

* Sensors:
  https://www.adafruit.com/product/1747
  https://www.adafruit.com/product/1748

* Datasheet:
  https://cdn-shop.adafruit.com/datasheets/MLX90614.pdf

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://github.com/adafruit/circuitpython/releases
"""

from micropython import const

import adafruit_bus_device.i2c_device as i2c_device


# imports

__version__ = "1.2.4"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_mlx90614.git"

# Internal constants:
_MLX90614_I2CADDR = const(0x5A)

# RAM
_MLX90614_RAWIR1 = const(0x04)
_MLX90614_RAWIR2 = const(0x05)
_MLX90614_TA = const(0x06)
_MLX90614_TOBJ1 = const(0x07)
_MLX90614_TOBJ2 = const(0x08)

# EEPROM
_MLX90614_TOMAX = const(0x20)
_MLX90614_TOMIN = const(0x21)
_MLX90614_PWMCTRL = const(0x22)
_MLX90614_TARANGE = const(0x23)
_MLX90614_EMISS = const(0x24)
_MLX90614_CONFIG = const(0x25)
_MLX90614_ADDR = const(0x0E)
_MLX90614_ID1 = const(0x3C)
_MLX90614_ID2 = const(0x3D)
_MLX90614_ID3 = const(0x3E)
_MLX90614_ID4 = const(0x3F)


class MLX90614:
    """Create an instance of the MLX90614 temperature sensor.  You must pass in
    the following parameters:
    - i2c: An instance of the I2C bus connected to the sensor.
    - frequency=100000 - this sensor does not respond to the default 400000 i2c bus speed

    Optionally you can specify:
    - address: The I2C address of the sensor.
    If not specified the sensor's default value will be assumed."""

    def __init__(self, i2c_bus, address=_MLX90614_I2CADDR):
        self._device = i2c_device.I2CDevice(i2c_bus, address)
        self.buf = bytearray(2)
        self.buf[0] = _MLX90614_CONFIG

    @property
    def ambient_temperature(self):
        """Ambient Temperature in celsius."""
        return self._read_temp(_MLX90614_TA)

    @property
    def object_temperature(self):
        """Object Temperature in celsius."""
        return self._read_temp(_MLX90614_TOBJ1)

    def _read_temp(self, register):
        temp = self._read_16(register)
        temp *= 0.02
        temp -= 273.15
        return temp

    def _read_16(self, register):
        # Read and return a 16-bit unsigned big endian value read from the
        # specified 16-bit register address.
        with self._device as i2c:
            self.buf[0] = register
            i2c.write_then_readinto(self.buf, self.buf, out_end=1)
            return self.buf[1] << 8 | self.buf[0]
