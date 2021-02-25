# SPDX-FileCopyrightText: 2018 Kattni Rembor for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_featherwing.joy_featherwing`
====================================================

Helper for using the `Joy FeatherWing <https://www.adafruit.com/product/3632>`_.

* Author(s): Kattni Rembor
"""

__version__ = "1.13.3"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_FeatherWing.git"

import board
from micropython import const
import adafruit_seesaw.seesaw

BUTTON_A = const(1 << 6)
BUTTON_B = const(1 << 7)
BUTTON_Y = const(1 << 9)
BUTTON_X = const(1 << 10)
BUTTON_SELECT = const(1 << 14)


class JoyFeatherWing:
    """Class representing an `Adafruit Joy FeatherWing <https://www.adafruit.com/product/3632>`_.

    Automatically uses the feather's I2C bus."""

    def __init__(self, i2c=None):
        if i2c is None:
            i2c = board.I2C()
        self._seesaw = adafruit_seesaw.seesaw.Seesaw(i2c)
        self._seesaw.pin_mode_bulk(
            BUTTON_A | BUTTON_B | BUTTON_Y | BUTTON_X | BUTTON_SELECT,
            self._seesaw.INPUT_PULLUP,
        )

        # Initialise joystick_offset
        self._joystick_offset = (0, 0)

    @property
    def button_a(self):
        """Joy featherwing button A.

        .. image :: ../docs/_static/joy_featherwing/joy_featherwing_a.jpg
          :alt: Joy FeatherWing Button A

        This example prints when button A is pressed.

        .. code-block:: python

            from adafruit_featherwing import joy_featherwing
            import time

            wing = joy_featherwing.JoyFeatherWing()

            while True:
                if wing.button_a:
                print("Button A pressed!")

        """
        return self._check_button(BUTTON_A)

    @property
    def button_b(self):
        """Joy featherwing button B.

        .. image :: ../docs/_static/joy_featherwing/joy_featherwing_b.jpg
          :alt: Joy FeatherWing Button B

        This example prints when button B is pressed.

        .. code-block:: python

            from adafruit_featherwing import joy_featherwing
            import time

            wing = joy_featherwing.JoyFeatherWing()

            while True:
                if wing.button_b:
                print("Button B pressed!")

        """
        return self._check_button(BUTTON_B)

    @property
    def button_x(self):
        """Joy featherwing button X.

        .. image :: ../docs/_static/joy_featherwing/joy_featherwing_x.jpg
          :alt: Joy FeatherWing Button X

        This example prints when button X is pressed.

        .. code-block:: python

            from adafruit_featherwing import joy_featherwing
            import time

            wing = joy_featherwing.JoyFeatherWing()

            while True:
                if wing.button_x:
                print("Button X pressed!")

        """
        return self._check_button(BUTTON_X)

    @property
    def button_y(self):
        """Joy featherwing button Y.

        .. image :: ../docs/_static/joy_featherwing/joy_featherwing_y.jpg
          :alt: Joy FeatherWing Button Y

        This example prints when button Y is pressed.

        .. code-block:: python

            from adafruit_featherwing import joy_featherwing
            import time

            wing = joy_featherwing.JoyFeatherWing()

            while True:
                if wing.button_y:
                print("Button Y pressed!")

        """
        return self._check_button(BUTTON_Y)

    @property
    def button_select(self):
        """Joy featherwing button SELECT.

        .. image :: ../docs/_static/joy_featherwing/joy_featherwing_select.jpg
          :alt: Joy FeatherWing Button SELECT

        This example prints when button SELECT is pressed.

        .. code-block:: python

            from adafruit_featherwing import joy_featherwing
            import time

            wing = joy_featherwing.JoyFeatherWing()

            while True:
                if wing.button_select:
                print("Button SELECT pressed!")

        """
        return self._check_button(BUTTON_SELECT)

    def _check_button(self, button):
        """Utilises the seesaw to determine which button is being pressed."""
        buttons = self._seesaw.digital_read_bulk(button)
        return not buttons != 0

    @property
    def joystick_offset(self):
        """Offset used to correctly report (0, 0) when the joystick is centered.

        .. image :: ../docs/_static/joy_featherwing/joy_featherwing_joystick.jpg
          :alt: Joy FeatherWing Joystick

        Provide a tuple of (x, y) to set your joystick center to (0, 0).
        The offset you provide is subtracted from the current reading.
        For example, if your joystick reads as (-4, 0), you would enter
        (-4, 0) as the offset. The code will subtract -4 from -4, and 0
        from 0, returning (0, 0).

        This example supplies an offset for zeroing, and prints the
        coordinates of the joystick when it is moved.

        .. code-block:: python

            from adafruit_featherwing import joy_featherwing
            import time

            wing = joy_featherwing.JoyFeatherWing()
            last_x = 0
            last_y = 0

            while True:
                wing.joystick_offset = (-4, 0)
                x, y = wing.joystick
                if (abs(x - last_x) > 3) or (abs(y - last_y) > 3):
                    last_x = x
                    last_y = y
                    print(x, y)
                time.sleep(0.01)

        """
        return self._joystick_offset

    @joystick_offset.setter
    def joystick_offset(self, offset):
        self._joystick_offset = offset

    def zero_joystick(self):
        """Zeros the joystick by using current reading as (0, 0).
        Note: You must not be touching the joystick at the time of zeroing
        for it to be accurate.

        .. image :: ../docs/_static/joy_featherwing/joy_featherwing_joystick.jpg
          :alt: Joy FeatherWing Joystick

        This example zeros the joystick, and prints the coordinates of
        joystick when it is moved.

        .. code-block:: python

            from adafruit_featherwing import joy_featherwing
            import time

            wing = joy_featherwing.JoyFeatherWing()
            last_x = 0
            last_y = 0
            wing.zero_joystick()

            while True:
                x, y = wing.joystick
                if (abs(x - last_x) > 3) or (abs(y - last_y) > 3):
                    last_x = x
                    last_y = y
                    print(x, y)
                time.sleep(0.01)

        """
        self._joystick_offset = (0, 0)
        self._joystick_offset = self.joystick

    @property
    def joystick(self):
        """Joy FeatherWing joystick.

        .. image :: ../docs/_static/joy_featherwing/joy_featherwing_joystick.jpg
          :alt: Joy FeatherWing Joystick

        This example zeros the joystick, and prints the coordinates of
        joystick when it is moved.

        .. code-block:: python

            from adafruit_featherwing import joy_featherwing
            import time

            wing = joy_featherwing.JoyFeatherWing()
            last_x = 0
            last_y = 0
            wing.zero_joystick()

            while True:
                x, y = wing.joystick
                if (abs(x - last_x) > 3) or (abs(y - last_y) > 3):
                    last_x = x
                    last_y = y
                    print(x, y)
                time.sleep(0.01)
        """
        x = int(127 - self._seesaw.analog_read(2) / 4) - self._joystick_offset[0]
        y = int(self._seesaw.analog_read(3) / 4 - 127) - self._joystick_offset[1]
        return x, y
