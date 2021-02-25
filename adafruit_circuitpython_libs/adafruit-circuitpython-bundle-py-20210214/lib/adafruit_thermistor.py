# SPDX-FileCopyrightText: 2017 Scott Shawcroft for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_thermistor`
===========================================================

A thermistor is a resistor that varies with temperature. This driver takes the
parameters of that resistor and its series resistor to determine the current
temperature. To hook one up, connect an analog input pin to the connection
between the resistor and the thermistor.  Be careful to note if the thermistor
is connected on the high side (from analog input up to high logic level/3.3 or
5 volts) or low side (from analog input down to ground).  The initializer takes
an optional high_side boolean that defaults to True and indicates if that the
thermistor is connected on the high side vs. low side.

* Author(s): Scott Shawcroft

Implementation Notes
--------------------

**Hardware:**

* Adafruit `10K Precision Epoxy Thermistor - 3950 NTC <https://www.adafruit.com/products/372>`_
  (Product ID: 372)

* Adafruit `Circuit Playground Express <https://www.adafruit.com/products/3333>`_
  (Product ID: 3333)

**Software and Dependencies:**

* Adafruit CircuitPython firmware: https://github.com/adafruit/circuitpython/releases

**Notes:**

#. Check the datasheet of your thermistor for the values.
"""

import math
import analogio

__version__ = "3.3.4"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_Thermistor.git"


class Thermistor:
    """Thermistor driver"""

    def __init__(
        self,
        pin,
        series_resistor,
        nominal_resistance,
        nominal_temperature,
        b_coefficient,
        *,
        high_side=True
    ):
        # pylint: disable=too-many-arguments
        self.pin = analogio.AnalogIn(pin)
        self.series_resistor = series_resistor
        self.nominal_resistance = nominal_resistance
        self.nominal_temperature = nominal_temperature
        self.b_coefficient = b_coefficient
        self.high_side = high_side

    @property
    def temperature(self):
        """The temperature of the thermistor in celsius"""
        if self.high_side:
            # Thermistor connected from analog input to high logic level.
            reading = self.pin.value / 64
            reading = (1023 * self.series_resistor) / reading
            reading -= self.series_resistor
        else:
            # Thermistor connected from analog input to ground.
            reading = self.series_resistor / (65535.0 / self.pin.value - 1.0)

        steinhart = reading / self.nominal_resistance  # (R/Ro)
        steinhart = math.log(steinhart)  # ln(R/Ro)
        steinhart /= self.b_coefficient  # 1/B * ln(R/Ro)
        steinhart += 1.0 / (self.nominal_temperature + 273.15)  # + (1/To)
        steinhart = 1.0 / steinhart  # Invert
        steinhart -= 273.15  # convert to C

        return steinhart
