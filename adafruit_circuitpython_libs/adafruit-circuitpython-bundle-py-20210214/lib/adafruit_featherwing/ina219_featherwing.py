# SPDX-FileCopyrightText: 2018 Kattni Rembor for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_featherwing.ina219_featherwing`
====================================================

Helper for using the `INA219 FeatherWing <https://www.adafruit.com/product/3650>`_.

* Author(s): Kattni Rembor
"""

__version__ = "1.13.3"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_FeatherWing.git"

import board
import adafruit_ina219


class INA219FeatherWing:
    """Class representing an `Adafruit INA219 FeatherWing
    <https://www.adafruit.com/product/3650>`_.

    Automatically uses the feather's I2C bus."""

    def __init__(self, i2c=None):
        if i2c is None:
            i2c = board.I2C()
        self._ina219 = adafruit_ina219.INA219(i2c)

    @property
    def bus_voltage(self):
        """Bus voltage returns volts.

        .. image :: ../docs/_static/ina219_featherwing/ina219_featherwing.jpg
          :alt: INA219 Featherwing

        This example prints the bus voltage with the appropriate units.

        .. code-block:: python

            from adafruit_featherwing import ina219_featherwing
            import time

            ina219 = ina219_featherwing.INA219FeatherWing()

            while True:
                print("Bus Voltage: {} V".format(ina219.bus_voltage))
                time.sleep(0.5)

        """
        return self._ina219.bus_voltage

    @property
    def shunt_voltage(self):
        """Shunt voltage returns volts.

        .. image :: ../docs/_static/ina219_featherwing/ina219_featherwing.jpg
          :alt: INA219 Featherwing

        This example prints the shunt voltage with the appropriate units.

        .. code-block:: python

            from adafruit_featherwing import ina219_featherwing
            import time

            ina219 = ina219_featherwing.INA219FeatherWing()

            while True:
                print("Shunt Voltage: {} V".format(ina219.shunt_voltage))
                time.sleep(0.5)

        """
        return self._ina219.shunt_voltage

    @property
    def voltage(self):
        """Voltage, known as load voltage, is bus voltage plus shunt voltage. Returns volts.

        .. image :: ../docs/_static/ina219_featherwing/ina219_featherwing.jpg
          :alt: INA219 Featherwing

        This example prints the voltage with the appropriate units.

        .. code-block:: python

            from adafruit_featherwing import ina219_featherwing
            import time

            ina219 = ina219_featherwing.INA219FeatherWing()

            while True:
                print("Voltage: {} V".format(ina219.voltage))
                time.sleep(0.5)

        """
        voltage = self._ina219.bus_voltage + self._ina219.shunt_voltage
        return voltage

    @property
    def current(self):
        """Current returns mA.

        .. image :: ../docs/_static/ina219_featherwing/ina219_featherwing.jpg
          :alt: INA219 Featherwing

        This example prints the current with the appropriate units.

        .. code-block:: python

            from adafruit_featherwing import ina219_featherwing
            import time

            ina219 = ina219_featherwing.INA219FeatherWing()

            while True:
                print("Current: {} mA".format(ina219.current))
                time.sleep(0.5)

        """
        return self._ina219.current
