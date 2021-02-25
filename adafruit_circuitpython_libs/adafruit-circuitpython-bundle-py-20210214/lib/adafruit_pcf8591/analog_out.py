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
`analog_out`
==============================
AnalogOut for setting the included DAC to a given voltage.

* Author(s): Bryan Siepert
"""


class AnalogOut:
    """AnalogIn Mock Implementation for ADC Reads."""

    def __init__(self, pcf, dac_pin=0):
        """AnalogIn

        :param pcf: The pcf object.
        :param ~digitalio.DigitalInOut DAC pin: Required pin must be P4

        """
        self._pcf = pcf
        if dac_pin != 0:
            raise AttributeError("DAC pin must be adafruit_pcf8591.pcf8591.DAC_PIN")
        self._pin_setting = dac_pin
        self._pcf.dac_enabled = True

    @property
    def value(self):
        """Returns the currently set value of the DAC pin as an integer."""
        return self._value

    @value.setter
    def value(self, new_value):  # this may have to scale from 16-bit
        if new_value < 0 or new_value > 65535:
            raise ValueError("value must be a 16-bit integer from 0-65535")

        if not self._pcf.dac_enabled:
            raise RuntimeError(
                "Underlying DAC is disabled, likely due to callint `deinit`"
            )
        # underlying sensor is 8-bit, so scale accordingly
        self._pcf.write(new_value >> 8)
        self._value = new_value

    def deinit(self):
        """Disable the underlying DAC and release the reference to the PCF8591.
        Create a new AnalogOut to use it again."""
        self._pcf.dac_enabled = False
        self._pcf = None
