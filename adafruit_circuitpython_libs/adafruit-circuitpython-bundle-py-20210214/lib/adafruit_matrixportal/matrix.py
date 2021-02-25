# SPDX-FileCopyrightText: 2020 Melissa LeBlanc-Williams, written for Adafruit Industries
#
# SPDX-License-Identifier: Unlicense
"""
`adafruit_matrixportal.matrix`
================================================================================

Helper library for the MatrixPortal M4 or Adafruit RGB Matrix Shield + Metro M4 Airlift Lite.

* Author(s): Melissa LeBlanc-Williams

Implementation Notes
--------------------

**Hardware:**

* `Adafruit Matrix Portal <https://www.adafruit.com/product/4745>`_
* `Adafruit Metro M4 Express AirLift <https://www.adafruit.com/product/4000>`_
* `Adafruit RGB Matrix Shield <https://www.adafruit.com/product/2601>`_
* `64x32 RGB LED Matrix <https://www.adafruit.com/product/2278>`_

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://github.com/adafruit/circuitpython/releases

"""

import os
import board
import displayio
import rgbmatrix
import framebufferio


__version__ = "2.1.0"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_MatrixPortal.git"


class Matrix:
    """Class representing the Adafruit RGB Matrix. This is used to automatically
    initialize the display.

    :param int width: The width of the display in Pixels. Defaults to 64.
    :param int height: The height of the display in Pixels. Defaults to 32.
    :param int bit_depth: The number of bits per color channel. Defaults to 2.
    :param list alt_addr_pins: An alternate set of address pins to use. Defaults to None
    :param string color_order: A string containing the letter "R", "G", and "B" in the
                               order you want. Defaults to "RGB"
    :param int width: The total width of the display(s) in Pixels. Defaults to 64.
    :param int height: The total height of the display(s) in Pixels. Defaults to 32.
    :param bool Serpentine: Used when panels are arranged in a serpentine pattern rather
                            than a Z-pattern. Defaults to True.
    :param int tiles_rows: Used to indicate the number of rows the panels are arranged in.
                           Defaults to 1.
    """

    # pylint: disable=too-few-public-methods,too-many-branches,too-many-statements,too-many-locals
    def __init__(
        self,
        *,
        width=64,
        height=32,
        bit_depth=2,
        alt_addr_pins=None,
        color_order="RGB",
        serpentine=True,
        tile_rows=1
    ):

        panel_height = height // tile_rows

        if not isinstance(color_order, str):
            raise ValueError("color_index should be a string")
        color_order = color_order.lower()
        red_index = color_order.find("r")
        green_index = color_order.find("g")
        blue_index = color_order.find("b")
        if -1 in (red_index, green_index, blue_index):
            raise ValueError("color_order should contain R, G, and B")

        if "Matrix Portal M4" in os.uname().machine:
            # MatrixPortal M4 Board
            addr_pins = [board.MTX_ADDRA, board.MTX_ADDRB, board.MTX_ADDRC]
            if panel_height > 16:
                addr_pins.append(board.MTX_ADDRD)
            if panel_height > 32:
                addr_pins.append(board.MTX_ADDRE)
            rgb_pins = [
                board.MTX_R1,
                board.MTX_G1,
                board.MTX_B1,
                board.MTX_R2,
                board.MTX_G2,
                board.MTX_B2,
            ]
            clock_pin = board.MTX_CLK
            latch_pin = board.MTX_LAT
            oe_pin = board.MTX_OE
        elif "Feather" in os.uname().machine:
            # Feather Style Board
            if "nrf52" in os.uname().sysname:
                # nrf52840 Style Feather
                addr_pins = [board.D11, board.D5, board.D13]
                if panel_height > 16:
                    addr_pins.append(board.D9)
                rgb_pins = [board.D6, board.A5, board.A1, board.A0, board.A4, board.D11]
                clock_pin = board.D12
            else:
                addr_pins = [board.A5, board.A4, board.A3]
                if panel_height > 16:
                    addr_pins.append(board.A2)
                rgb_pins = [
                    board.D6,
                    board.D5,
                    board.D9,
                    board.D11,
                    board.D10,
                    board.D12,
                ]
                clock_pin = board.D13
            latch_pin = board.D0
            oe_pin = board.D1
        else:
            # Metro/Grand Central Style Board
            if alt_addr_pins is None and height <= 16:
                raise RuntimeError(
                    "Pin A2 unavailable in this mode. Please specify alt_addr_pins."
                )
            addr_pins = [board.A0, board.A1, board.A2, board.A3]
            rgb_pins = [board.D2, board.D3, board.D4, board.D5, board.D6, board.D7]
            clock_pin = board.A4
            latch_pin = board.D10
            oe_pin = board.D9

        # Alternate Address Pins
        if alt_addr_pins is not None:
            addr_pins = alt_addr_pins

        try:
            displayio.release_displays()
            if tile_rows > 1:
                matrix = rgbmatrix.RGBMatrix(
                    width=width,
                    height=height,
                    bit_depth=bit_depth,
                    rgb_pins=(
                        rgb_pins[red_index],
                        rgb_pins[green_index],
                        rgb_pins[blue_index],
                        rgb_pins[red_index + 3],
                        rgb_pins[green_index + 3],
                        rgb_pins[blue_index + 3],
                    ),
                    addr_pins=addr_pins,
                    clock_pin=clock_pin,
                    latch_pin=latch_pin,
                    output_enable_pin=oe_pin,
                    tile=tile_rows,
                    serpentine=serpentine,
                )
            else:
                matrix = rgbmatrix.RGBMatrix(
                    width=width,
                    height=height,
                    bit_depth=bit_depth,
                    rgb_pins=(
                        rgb_pins[red_index],
                        rgb_pins[green_index],
                        rgb_pins[blue_index],
                        rgb_pins[red_index + 3],
                        rgb_pins[green_index + 3],
                        rgb_pins[blue_index + 3],
                    ),
                    addr_pins=addr_pins,
                    clock_pin=clock_pin,
                    latch_pin=latch_pin,
                    output_enable_pin=oe_pin,
                )
            self.display = framebufferio.FramebufferDisplay(matrix)
        except TypeError:
            if tile_rows > 1:
                raise RuntimeError(
                    "Make sure you are running CircuitPython 6.2.0.alpha-1 or later"
                ) from TypeError
            raise
        except ValueError:
            raise RuntimeError("Failed to initialize RGB Matrix") from ValueError
