# SPDX-FileCopyrightText: Copyright (c) 2020 Bryan Siepert for Adafruit Industries
#
# SPDX-License-Identifier: MIT

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
"""
`analog_in`
==============================
AnalogIn for ADC readings.

* Author(s): Bryan Siepert, adpted from ADS1x15 by Carter Nelson
"""


class AnalogIn:
    """AnalogIn Mock Implementation for ADC Reads."""

    def __init__(self, pcf, pin):
        """AnalogIn

        :param ads: The PCF8591 object.
        :param ~digitalio.DigitalInOut pin: Required ADC channel pin.

        """
        self._pcf = pcf
        self._channel_number = pin

    @property
    def voltage(self):
        """Returns the value of an ADC channel in volts as compared to the reference voltage."""

        if not self._pcf:
            raise RuntimeError(
                "Underlying ADC does not exist, likely due to callint `deinit`"
            )
        raw_reading = self._pcf.read(self._channel_number)
        return ((raw_reading << 8) / 65535) * self._pcf.reference_voltage

    @property
    def value(self):
        """Returns the value of an ADC channel.
        The value is scaled to a 16-bit integer from the native 8-bit value."""

        if not self._pcf:
            raise RuntimeError(
                "Underlying ADC does not exist, likely due to callint `deinit`"
            )

        return self._pcf.read(self._channel_number) << 8

    @property
    def reference_voltage(self):
        """The maximum voltage measurable (also known as the reference voltage) as a float in
        Volts. Assumed to be 3.3V but can be overridden using the `PCF8591` constructor"""
        if not self._pcf:
            raise RuntimeError(
                "Underlying ADC does not exist, likely due to callint `deinit`"
            )
        return self._pcf.reference_voltage

    def deinit(self):
        """Release the reference to the PCF8591. Create a new AnalogIn to use it again."""
        self._pcf = None
