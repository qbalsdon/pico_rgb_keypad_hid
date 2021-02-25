# SPDX-FileCopyrightText: 2020 Kattni Rembor for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_pybadger.cpb_gizmo`
================================================================================

Badge-focused CircuitPython helper library for Circuit Playground Bluefruit with TFT Gizmo.


* Author(s): Kattni Rembor

Implementation Notes
--------------------

**Hardware:**

* `Adafruit Circuit Playground Bluefruit <https://www.adafruit.com/product/4333>`_
* `Adafruit TFT Gizmo <https://www.adafruit.com/product/4367>`_

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://github.com/adafruit/circuitpython/releases

"""

from collections import namedtuple
import board
import digitalio
import analogio
import busio
import audiopwmio
from adafruit_gizmo import tft_gizmo
from gamepad import GamePad
import adafruit_lis3dh
import neopixel
from adafruit_pybadger.pybadger_base import PyBadgerBase

__version__ = "3.2.2"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_PyBadger.git"

Buttons = namedtuple("Buttons", "a b")


class CPB_Gizmo(PyBadgerBase):
    """Class that represents a single Circuit Playground Bluefruit with TFT Gizmo."""

    display = None
    _audio_out = audiopwmio.PWMAudioOut
    _neopixel_count = 10

    def __init__(self):
        super().__init__()

        _i2c = busio.I2C(board.ACCELEROMETER_SCL, board.ACCELEROMETER_SDA)
        _int1 = digitalio.DigitalInOut(board.ACCELEROMETER_INTERRUPT)
        self.accelerometer = adafruit_lis3dh.LIS3DH_I2C(_i2c, address=0x19, int1=_int1)
        self.accelerometer.range = adafruit_lis3dh.RANGE_8_G

        self.display = tft_gizmo.TFT_Gizmo()
        self._display_brightness = 1.0

        # NeoPixels
        self._neopixels = neopixel.NeoPixel(
            board.NEOPIXEL, self._neopixel_count, brightness=1, pixel_order=neopixel.GRB
        )
        _a_btn = digitalio.DigitalInOut(board.BUTTON_A)
        _a_btn.switch_to_input(pull=digitalio.Pull.DOWN)
        _b_btn = digitalio.DigitalInOut(board.BUTTON_B)
        _b_btn.switch_to_input(pull=digitalio.Pull.DOWN)
        self._buttons = GamePad(_a_btn, _b_btn)
        self._light_sensor = analogio.AnalogIn(board.LIGHT)

    @property
    def button(self):
        """The buttons on the board.

        Example use:

        .. code-block:: python

          from adafruit_pybadger import pybadger

          while True:
              if pybadger.button.a:
                  print("Button A")
              elif pybadger.button.b:
                  print("Button B")
        """
        button_values = self._buttons.get_pressed()
        return Buttons(
            button_values & PyBadgerBase.BUTTON_B, button_values & PyBadgerBase.BUTTON_A
        )

    @property
    def _unsupported(self):
        """This feature is not supported on CPB Gizmo."""
        raise NotImplementedError("This feature is not supported on CPB Gizmo.")

    # The following is a list of the features available in other PyBadger modules but
    # not available for CPB Gizmo. If called while using a CPB Gizmo, they will result in the
    # NotImplementedError raised in the property above.


cpb_gizmo = CPB_Gizmo()  # pylint: disable=invalid-name
"""Object that is automatically created on import."""
