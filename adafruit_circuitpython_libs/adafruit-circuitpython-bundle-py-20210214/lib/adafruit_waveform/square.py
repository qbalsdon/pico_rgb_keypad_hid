# SPDX-FileCopyrightText: 2017 Scott Shawcroft for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_waveform.square`
====================================================

This library generates squard waveforms that can be used to generate
squard audio signals.

* Author(s): Scott Shawcroft, BrentRu
"""

import array

__version__ = "1.3.5"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_Waveform.git"


def square_wave(sample_length=2):
    """Generate a single square wave of sample_length size"""
    square = array.array("H", [0] * sample_length)
    for i in range(sample_length // 2):
        square[i] = 0xFFFF
    return square
