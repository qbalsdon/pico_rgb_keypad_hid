# SPDX-FileCopyrightText: 2020 Melissa LeBlanc-Williams, written for Adafruit Industries
#
# SPDX-License-Identifier: Unlicense
"""
`adafruit_matrixportal.graphics`
================================================================================

Helper library for the MatrixPortal M4 or Adafruit RGB Matrix Shield + Metro M4 Airlift Lite.

* Author(s): Melissa LeBlanc-Williams

Implementation Notes
--------------------

**Hardware:**

* `Adafruit MatrixPortal M4 <https://www.adafruit.com/product/4745>`_
* `Adafruit Metro M4 Express AirLift <https://www.adafruit.com/product/4000>`_
* `Adafruit RGB Matrix Shield <https://www.adafruit.com/product/2601>`_
* `64x32 RGB LED Matrix <https://www.adafruit.com/product/2278>`_

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://github.com/adafruit/circuitpython/releases

"""

from adafruit_portalbase.graphics import GraphicsBase
from adafruit_matrixportal.matrix import Matrix

__version__ = "2.1.0"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_MatrixPortal.git"


class Graphics(GraphicsBase):
    """Graphics Helper Class for the MatrixPortal Library

    :param default_bg: The path to your default background image file or a hex color.
                       Defaults to 0x000000.
    :param int width: The total width of the display(s) in Pixels. Defaults to 64.
    :param int height: The total height of the display(s) in Pixels. Defaults to 32.
    :param int bit_depth: The number of bits per color channel. Defaults to 2.
    :param list alt_addr_pins: An alternate set of address pins to use. Defaults to None
    :param string color_order: A string containing the letter "R", "G", and "B" in the
                               order you want. Defaults to "RGB"
    :param bool Serpentine: Used when panels are arranged in a serpentine pattern rather
                            than a Z-pattern. Defaults to True.
    :param int tiles_rows: Used to indicate the number of rows the panels are arranged in.
                           Defaults to 1.
    :param debug: Turn on debug print outs. Defaults to False.

    """

    # pylint: disable=too-few-public-methods
    def __init__(
        self,
        *,
        default_bg=0x000000,
        width=64,
        height=32,
        bit_depth=2,
        alt_addr_pins=None,
        color_order="RGB",
        serpentine=True,
        tile_rows=1,
        debug=False
    ):

        matrix = Matrix(
            bit_depth=bit_depth,
            width=width,
            height=height,
            alt_addr_pins=alt_addr_pins,
            color_order=color_order,
            serpentine=serpentine,
            tile_rows=tile_rows,
        )

        super().__init__(matrix.display, default_bg=default_bg, debug=debug)
