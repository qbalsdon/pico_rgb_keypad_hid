# SPDX-FileCopyrightText: 2017 Michael McWethy for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`colorutility`
====================================================

Helper functions for color calculations

* Author(s): Michael McWethy
"""

__version__ = "2.2.5"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_APDS9960.git"


def calculate_color_temperature(r, g, b):
    """Converts the raw R/G/B values to color temperature in degrees Kelvin"""

    #  1. Map RGB values to their XYZ counterparts.
    #   Based on 6500K fluorescent, 3000K fluorescent
    #    and 60W incandescent values for a wide range.
    #    Note: Y = Illuminance or lux
    x = (-0.14282 * r) + (1.54924 * g) + (-0.95641 * b)
    y = (-0.32466 * r) + (1.57837 * g) + (-0.73191 * b)
    z = (-0.68202 * r) + (0.77073 * g) + (0.56332 * b)

    #  2. Calculate the chromaticity co-ordinates
    xchrome = x / (x + y + z)
    ychrome = y / (x + y + z)

    #  3. Use   to determine the CCT
    n = (xchrome - 0.3320) / (0.1858 - ychrome)

    #  4. Calculate the final CCT
    cct = (449.0 * pow(n, 3)) + (3525.0 * pow(n, 2)) + (6823.3 * n) + 5520.33

    #    Return the results in degrees Kelvin
    return cct


def calculate_lux(r, g, b):
    """Calculate ambient light values"""
    #   This only uses RGB ... how can we integrate clear or calculate lux
    #   based exclusively on clear since this might be more reliable?
    illuminance = (-0.32466 * r) + (1.57837 * g) + (-0.73191 * b)

    return illuminance
