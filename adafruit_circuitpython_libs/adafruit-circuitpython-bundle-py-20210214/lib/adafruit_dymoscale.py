# SPDX-FileCopyrightText: 2019 ladyada for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_dymoscale`
================================================================================

CircuitPython interface for DYMO scales.


* Author(s): ladyada

Implementation Notes
--------------------

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://github.com/adafruit/circuitpython/releases
"""

import time
from pulseio import PulseIn
from micropython import const

OUNCES = const(0x0B)  # data in weight is in ounces
GRAMS = const(0x02)  # data in weight is in grams
PULSE_WIDTH = 72.5

__version__ = "1.1.3"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_DymoScale.git"

# pylint: disable=too-few-public-methods
class ScaleReading:
    """Dymo Scale Data"""

    units = None  # what units we're measuring
    stable = None  # is the measurement stable?
    weight = None  # the weight!


class DYMOScale:
    """Interface to a DYMO postal scale."""

    def __init__(self, data_pin, units_pin, timeout=1.0):
        """Sets up a DYMO postal scale.
        :param ~pulseio.PulseIn data_pin: The data pin from the Dymo scale.
        :param ~digitalio.DigitalInOut units_pin: The grams/oz button from the Dymo scale.
        :param double timeout: The timeout, in seconds.
        """
        self.timeout = timeout
        # set up the toggle pin
        self.units_pin = units_pin
        # set up the dymo data pin
        self.dymo = PulseIn(data_pin, maxlen=96, idle_state=True)

    @property
    def weight(self):
        """Weight in grams"""
        reading = self.get_scale_data()
        if reading.units == OUNCES:
            reading.weight *= 28.35
        reading.units = GRAMS
        return reading

    def toggle_unit_button(self, switch_units=False):
        """Toggles the unit button on the dymo.
        :param bool switch_units: Simulates pressing the units button.
        """
        toggle_times = 0
        if switch_units:  # press the button once
            toggle_amt = 2
        else:  # toggle and preserve current unit state
            toggle_amt = 4
        while toggle_times < toggle_amt:
            self.units_pin.value ^= 1
            time.sleep(2)
            toggle_times += 1

    def _read_pulse(self):
        """Reads a pulse of SPI data on a pin that corresponds to DYMO scale
        output protocol (12 bytes of data at about 14KHz).
        """
        timestamp = time.monotonic()
        self.dymo.pause()
        self.dymo.clear()
        self.dymo.resume()
        while len(self.dymo) < 35:
            if (time.monotonic() - timestamp) > self.timeout:
                raise RuntimeError(
                    "Timed out waiting for data - is the scale turned on?"
                )
        self.dymo.pause()

    def get_scale_data(self):
        """Reads a pulse of SPI data and analyzes the resulting data."""
        self._read_pulse()
        bits = [0] * 96  # there are 12 bytes = 96 bits of data
        bit_idx = 0  # we will count a bit at a time
        bit_val = False  # first pulses will be LOW
        for i in range(len(self.dymo)):
            if self.dymo[i] == 65535:  # check for the pulse between transmits
                break
            num_bits = int(
                self.dymo[i] / PULSE_WIDTH + 0.5
            )  # ~14KHz == ~7.5us per clock
            bit = 0
            while bit < num_bits:
                bits[bit_idx] = bit_val
                bit_idx += 1
                if bit_idx == 96:  # we have read all the data we wanted
                    break
                bit += 1
            bit_val = not bit_val
        data_bytes = [0] * 12  # alllocate data array
        for byte_n in range(12):
            the_byte = 0
            for bit_n in range(8):
                the_byte <<= 1
                the_byte |= bits[byte_n * 8 + bit_n]
            data_bytes[byte_n] = the_byte
        # do some very basic data checking
        if data_bytes[0] != 3 and data_bytes[0] != 2:
            raise RuntimeError("Bad data capture")
        if data_bytes[1] != 3 or data_bytes[7] != 4 or data_bytes[8] != 0x1C:
            raise RuntimeError("Bad data capture")
        if data_bytes[9] != 0 or data_bytes[10] or data_bytes[11] != 0:
            raise RuntimeError("Bad data capture")
        reading = ScaleReading()
        # parse out the data_bytes
        reading.stable = data_bytes[2] & 0x4
        reading.units = data_bytes[3]
        reading.weight = data_bytes[5] + (data_bytes[6] << 8)
        if data_bytes[2] & 0x1:
            reading.weight *= -1
        if reading.units == OUNCES:
            if data_bytes[4] & 0x80:
                data_bytes[4] -= 0x100
            reading.weight *= 10 ** data_bytes[4]
        return reading
