# SPDX-FileCopyrightText: 2017 PaintYourDragon for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_fancyled.fastled_helpers`
====================================================

CircuitPython "helper" library based on the Arduino FastLED library.
Uses similar function names to assist with porting of existing Arduino FastLED
projects to CircuitPython.

* Author(s): PaintYourDragon
"""

# imports

__version__ = "1.4.4"
__repo__ = "https://github.com/Adafruit/Adafruit_CircuitPython_FancyLED.git"

from math import floor
from adafruit_fancyled import adafruit_fancyled as fancy

# These are helper functions that provide more FastLED-like calls for
# fancyled functions.
# Function names are kept the same as FastLED, which normally upsets pylint.
# Disable name-checking so this passes muster.
# pylint: disable=invalid-name

GFACTOR = 2.5  # Default gamma-correction factor for function below


def applyGamma_video(n, g_r=GFACTOR, g_g=None, g_b=None, inplace=False):
    """Approximates various invocations of FastLED's many-ways-overloaded
    applyGamma_video() function.

    ACCEPTS: One of three ways:
      1. A single brightness level (0-255) and optional gamma-correction
         factor (float usu. > 1.0, default if unspecified is 2.5).
      2. A single CRGB, CHSV or packed integer type and optional gamma
         factor or separate R, G, B gamma values.
      3. A list of CRGB, CHSV or packed integer types (and optional gamma(s)).

      In the tuple/list cases, the 'inplace' flag determines whether
      a new tuple/list is calculated and returned, or the existing
      value is modified in-place.  By default this is 'False'.
      Can also use the napplyGamma_video() function to more directly
      approximate FastLED syntax/behavior.

    RETURNS: Corresponding to above cases:
      1. Single gamma-corrected brightness level (0-255).
      2. A gamma-corrected CRGB value (even if input is CHSV or packed).
      3. A list of gamma-corrected CRGB values.

      In the tuple/list cases, there is NO return value if 'inplace'
      is true -- the original values are modified.
    """

    # If single gamma value is passed, keep that, otherwise convert
    # gamma values to tuple for gamma_adjust function.
    if g_g is not None and g_b is not None:
        g_r = (g_r, g_g, g_b)

    return fancy.gamma_adjust(n, g_r, inplace=inplace)


def napplyGamma_video(n, g_r=GFACTOR, g_g=None, g_b=None):
    """In-place version of applyGamma_video() (to mimic FastLED function
    name).  This is for RGB tuples and tuple lists (not the prior function's
    integer case)
    """

    return applyGamma_video(n, g_r, g_g, g_b, inplace=True)


def loadDynamicGradientPalette(src, size):
    """Kindasorta like FastLED's loadDynamicGradientPalette() function,
    with some gotchas.

    ACCEPTS: Gradient palette data as a 'bytes' type (makes it easier to copy
             over gradient palettes from existing FastLED Arduino sketches)...
             each palette entry is four bytes: a relative position (0-255)
             within the overall resulting palette (whatever its size), and
             3 values for R, G and B...and a length for a new palette list
             to be allocated.

    RETURNS: list of CRGB colors.
    """

    # Convert gradient from bytelist (groups of 4) to list of tuples,
    # each consisting of a position (0.0 to 1.0) and CRGB color.
    # (This is what FancyLED's expand_gradient needs for input.)
    grad = []
    for i in range(0, len(src), 4):
        grad.append((src[i] / 255.0, fancy.CRGB(src[i + 1], src[i + 2], src[i + 3])))

    # Create palette (CRGB list) matching 'size' length
    return fancy.expand_gradient(grad, size)


def ColorFromPalette(pal, pos, brightness=255, blend=False):
    """Approximates the FastLED ColorFromPalette() function

    ACCEPTS: color palette (list of CRGB, CSHV and/or packed ints),
             palette index (x16) + blend factor of next index (0-15) --
             e.g. pass 32 to retrieve palette index 2, or 40 for an
             interpolated value between palette index 2 and 3, optional
             brightness (0-255), optional blend flag (True/False)

    RETURNS: CRGB color, no gamma correction
    """

    # Alter 'pos' from FastLED-like behavior to fancyled range
    if blend:
        # Continuous interpolation 0.0 to 1.0
        pos = (pos / 16.0) / len(pal)
    else:
        # No blending -- quantize to nearest palette bin
        pos = floor(pos / 16.0) / len(pal)

    color = fancy.palette_lookup(pal, pos)

    if brightness < 1.0:
        brightness /= 255.0
        if isinstance(color, fancy.CHSV):
            color = fancy.CRGB(color)
        elif isinstance(color, int):
            color = fancy.unpack(color)
        color.red *= brightness
        color.green *= brightness
        color.blue *= brightness

    return color


def hsv2rgb_spectrum(hue, sat, val):

    """This is named the same thing as FastLED's simpler HSV to RGB function
    (spectrum, vs rainbow) but implementation is a bit different for the
    sake of getting something running (adapted from some NeoPixel code).

    ACCEPTS: hue, saturation, value in range 0 to 255
    RETURNS: CRGB color.
    """

    return fancy.CRGB(fancy.CHSV(hue / 255, sat / 255, val / 255))


# pylint: enable=invalid-name
