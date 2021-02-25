# SPDX-FileCopyrightText: 2019 Melissa LeBlanc-Williams for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_featherwing.tempmotion_featherwing`
====================================================

Helper for using the `Adafruit ADXL343 + ADT7410 Sensor FeatherWing
<https://www.adafruit.com/product/4147>`_.

* Author(s): Melissa LeBlanc-Williams
"""

__version__ = "1.13.3"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_FeatherWing.git"

import board
import adafruit_adxl34x
import adafruit_adt7410


class TempMotionFeatherWing:
    """Class helper representing an `Adafruit ADXL343 + ADT7410 Sensor FeatherWing
    <https://www.adafruit.com/product/4147>`_.

    Automatically uses the feather's I2C bus."""

    def __init__(self, adxl343_address=0x53, adt7410_address=0x48, i2c=None):
        if i2c is None:
            i2c = board.I2C()
        self._adxl343 = adafruit_adxl34x.ADXL345(i2c, address=adxl343_address)
        self._adt7410 = adafruit_adt7410.ADT7410(i2c, address=adt7410_address)

    @property
    def temperature(self):
        """Returns ADT7410 Temperature"""
        return self._adt7410.temperature

    @property
    def status(self):
        """Returns the ADT7410 Status"""
        return self._adt7410.status

    @property
    def configuration(self):
        """Returns the ADT7410 Configuration"""
        return self._adt7410.configuration

    @configuration.setter
    def configuration(self, val):
        self._adt7410.configuration = val

    @property
    def acceleration(self):
        """Returns the ADXL343 Acceleration"""
        return self._adxl343.acceleration

    @property
    def events(self):
        """Returns the ADXL343 Enabled Events"""
        return self._adxl343.events

    def enable_motion_detection(self, **kwargs):
        """Enable motion detection"""
        self._adxl343.enable_motion_detection(**kwargs)

    def disable_motion_detection(self):
        """Disable motion detection"""
        self._adxl343.disable_motion_detection()

    def enable_freefall_detection(self, **kwargs):
        """Enable freefall detection"""
        self._adxl343.enable_freefall_detection(**kwargs)

    def disable_freefall_detection(self):
        """Disable freefall detection"""
        self._adxl343.disable_freefall_detection()

    def enable_tap_detection(self, **kwargs):
        """Enable freefall detection"""
        self._adxl343.enable_tap_detection(**kwargs)

    def disable_tap_detection(self):
        """Disable freefall detection"""
        self._adxl343.disable_tap_detection()

    @property
    def data_rate(self):
        """The data rate of the sensor."""
        return self._adxl343.data_rate

    @data_rate.setter
    def data_rate(self, val):
        self._adxl343.data_rate = val

    @property
    def range(self):
        """The measurement range of the sensor."""
        return self._adxl343.range

    @range.setter
    def range(self, val):
        self._adxl343.range = val
