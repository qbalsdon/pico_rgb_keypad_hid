# SPDX-FileCopyrightText: 2019 Melissa LeBlanc-Williams for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_featherwing.dotstar_featherwing`
====================================================

Helper for using the `DotStar FeatherWing <https://www.adafruit.com/product/3449>`_.

* Author(s): Melissa LeBlanc-Williams
"""

__version__ = "1.13.3"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_FeatherWing.git"

import board
import adafruit_dotstar as dotstar
from adafruit_featherwing.pixelmatrix import PixelMatrix


class DotStarFeatherWing(PixelMatrix):
    """Class representing a `DotStar FeatherWing
    <https://www.adafruit.com/product/3449>`_.

    The feather uses pins D13 and D11"""

    def __init__(self, clock=board.D13, data=board.D11, brightness=0.2):
        """
        :param pin clock: The clock pin for the featherwing
        :param pin data: The data pin for the featherwing
        :param float brightness: Optional brightness (0.0-1.0) that defaults to 1.0
        """
        super().__init__()
        self.rows = 6
        self.columns = 12
        self._matrix = dotstar.DotStar(
            clock,
            data,
            self.rows * self.columns,
            brightness=brightness,
            auto_write=False,
        )
