# SPDX-FileCopyrightText: 2020 Kattni Rembor for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_pybadger.pygamer`
================================================================================

Badge-focused CircuitPython helper library for PyGamer.


* Author(s): Kattni Rembor

Implementation Notes
--------------------

**Hardware:**

* `Adafruit PyGamer <https://www.adafruit.com/product/4277>`_

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://github.com/adafruit/circuitpython/releases

"""

from collections import namedtuple
import board
import analogio
import digitalio
import audioio
import neopixel
from gamepadshift import GamePadShift
import adafruit_lis3dh
from adafruit_pybadger.pybadger_base import PyBadgerBase

__version__ = "3.2.2"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_PyBadger.git"

Buttons = namedtuple("Buttons", "b a start select right down up left")


class PyGamer(PyBadgerBase):
    """Class that represents a single PyGamer."""

    _audio_out = audioio.AudioOut
    _neopixel_count = 5

    def __init__(self):
        super().__init__()

        i2c = board.I2C()

        int1 = digitalio.DigitalInOut(board.ACCELEROMETER_INTERRUPT)
        try:
            self._accelerometer = adafruit_lis3dh.LIS3DH_I2C(
                i2c, address=0x19, int1=int1
            )
        except ValueError:
            self._accelerometer = adafruit_lis3dh.LIS3DH_I2C(i2c, int1=int1)

        # NeoPixels
        self._neopixels = neopixel.NeoPixel(
            board.NEOPIXEL, self._neopixel_count, brightness=1, pixel_order=neopixel.GRB
        )

        self._buttons = GamePadShift(
            digitalio.DigitalInOut(board.BUTTON_CLOCK),
            digitalio.DigitalInOut(board.BUTTON_OUT),
            digitalio.DigitalInOut(board.BUTTON_LATCH),
        )

        self._pygamer_joystick_x = analogio.AnalogIn(board.JOYSTICK_X)
        self._pygamer_joystick_y = analogio.AnalogIn(board.JOYSTICK_Y)

        self._light_sensor = analogio.AnalogIn(board.A7)

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
              elif pybadger.button.start:
                  print("Button start")
              elif pybadger.button.select:
                  print("Button select")

        """
        button_values = self._buttons.get_pressed()
        x, y = self.joystick
        return Buttons(
            button_values & PyBadgerBase.BUTTON_B,
            button_values & PyBadgerBase.BUTTON_A,
            button_values & PyBadgerBase.BUTTON_START,
            button_values & PyBadgerBase.BUTTON_SELECT,
            x > 50000,  # RIGHT
            y > 50000,  # DOWN
            y < 15000,  # UP
            x < 15000,  # LEFT
        )

    @property
    def joystick(self):
        """The joystick on the PyGamer."""
        x = self._pygamer_joystick_x.value
        y = self._pygamer_joystick_y.value
        return x, y


pygamer = PyGamer()  # pylint: disable=invalid-name
"""Object that is automatically created on import."""
