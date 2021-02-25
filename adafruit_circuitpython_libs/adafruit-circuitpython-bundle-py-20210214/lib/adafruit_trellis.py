# SPDX-FileCopyrightText: 2018 ladyada for Adafruit Industries
# SPDX-FileCopyrightText: 2018 Michael Schroeder (sommersoft)
#
# SPDX-License-Identifier: MIT

#  This is a library for the Adafruit Trellis w/HT16K33
#
#  Designed specifically to work with the Adafruit Trellis
#  ----> https://www.adafruit.com/products/1616
#  ----> https://www.adafruit.com/products/1611
#
#  These displays use I2C to communicate, 2 pins are required to
#  interface
#  Adafruit invests time and resources providing this open source code,
#  please support Adafruit and open-source hardware by purchasing
#  products from Adafruit!
#
#  Also utilized functions from the CircuitPython HT16K33 library
#  written by Radomir Dopieralski & Tony DiCola for Adafruit Industries
#  https://github.com/adafruit/Adafruit_CircuitPython_HT16K33

"""
`adafruit_trellis` - Adafruit Trellis Monochrome 4x4 LED Backlit Keypad
=========================================================================

CircuitPython library to support Adafruit's Trellis Keypad.

* Author(s): Limor Fried, Radomir Dopieralski, Tony DiCola,
             Scott Shawcroft, and Michael Schroeder

Implementation Notes
--------------------

**Hardware:**

* Adafruit `Trellis Monochrome 4x4 LED Backlit Keypad
  <https://www.adafruit.com/product/1616>`_ (Product ID: 1616)

**Software and Dependencies:**

* Adafruit CircuitPython firmware (2.2.0+) for the ESP8622 and M0-based boards:
  https://github.com/adafruit/circuitpython/releases
* Adafruit's Bus Device library: https://github.com/adafruit/Adafruit_CircuitPython_BusDevice
"""

__version__ = "1.3.6"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_Trellis.git"

from micropython import const
from adafruit_bus_device import i2c_device

# HT16K33 Command Contstants
_HT16K33_OSCILATOR_ON = const(0x21)
_HT16K33_BLINK_CMD = const(0x80)
_HT16K33_BLINK_DISPLAYON = const(0x01)
_HT16K33_CMD_BRIGHTNESS = const(0xE0)
_HT16K33_KEY_READ_CMD = const(0x40)

# LED Lookup Table
ledLUT = (
    0x3A,
    0x37,
    0x35,
    0x34,
    0x28,
    0x29,
    0x23,
    0x24,
    0x16,
    0x1B,
    0x11,
    0x10,
    0x0E,
    0x0D,
    0x0C,
    0x02,
)

# Button Loookup Table
buttonLUT = (
    0x07,
    0x04,
    0x02,
    0x22,
    0x05,
    0x06,
    0x00,
    0x01,
    0x03,
    0x10,
    0x30,
    0x21,
    0x13,
    0x12,
    0x11,
    0x31,
)
# pylint: disable=missing-docstring, protected-access
class TrellisLEDs:
    def __init__(self, trellis_obj):
        self._parent = trellis_obj

    def __getitem__(self, x):
        if 0 < x >= self._parent._num_leds:
            raise ValueError(
                ("LED number must be between 0 -", self._parent._num_leds - 1)
            )
        led = ledLUT[x % 16] >> 4
        mask = 1 << (ledLUT[x % 16] & 0x0F)
        return bool(
            (
                (
                    self._parent._led_buffer[x // 16][(led * 2) + 1]
                    | self._parent._led_buffer[x // 16][(led * 2) + 2] << 8
                )
                & mask
            )
            > 0
        )

    def __setitem__(self, x, value):
        if 0 < x >= self._parent._num_leds:
            raise ValueError(
                ("LED number must be between 0 -", self._parent._num_leds - 1)
            )
        led = ledLUT[x % 16] >> 4
        mask = 1 << (ledLUT[x % 16] & 0x0F)
        if value:
            self._parent._led_buffer[x // 16][(led * 2) + 1] |= mask & 0xFF
            self._parent._led_buffer[x // 16][(led * 2) + 2] |= mask >> 8
        elif not value:
            self._parent._led_buffer[x // 16][(led * 2) + 1] &= ~mask
            self._parent._led_buffer[x // 16][(led * 2) + 2] &= ~mask >> 8
        else:
            raise ValueError("LED value must be True or False")

        if self._parent._auto_show:
            self._parent.show()

    # pylint: disable=invalid-name
    def fill(self, on):
        fill = 0xFF if on else 0x00
        for buff in range(len(self._parent._i2c_devices)):
            for i in range(1, 17):
                self._parent._led_buffer[buff][i] = fill
        if self._parent._auto_show:
            self._parent.show()


# pylint: enable=missing-docstring, protected-access


class Trellis:
    """
    Driver base for a single Trellis Board

    :param ~busio.I2C i2c: The `busio.I2C` object to use. This is the only required parameter
                           when using a single Trellis board.
    :param list addresses: The I2C address(es) of the Trellis board(s) you're using. Defaults
                           to ``[0x70]`` which is the default address for Trellis boards. See
                           Trellis product guide for using different/multiple I2C addresses.
                           https://learn.adafruit.com/adafruit-trellis-diy-open-source-led-keypad


    .. literalinclude:: ../examples/trellis_simpletest.py
        :caption: Usage Example
        :linenos:

    """

    def __init__(self, i2c, addresses=None):
        if addresses is None:
            addresses = [0x70]
        self._i2c_devices = []
        self._led_buffer = []
        self._buttons = []
        for i2c_address in addresses:
            self._i2c_devices.append(i2c_device.I2CDevice(i2c, i2c_address))
            self._led_buffer.append(bytearray(17))
            self._buttons.append([bytearray(6), bytearray(6)])
        self._num_leds = len(self._i2c_devices) * 16
        self._temp = bytearray(1)
        self._blink_rate = None
        self._brightness = None
        self._auto_show = True
        self.led = TrellisLEDs(self)
        """
        The LED object used to interact with Trellis LEDs.

        - ``trellis.led[x]`` returns the current LED status of LED ``x`` (True/False)
        - ``trellis.led[x] = True`` turns the LED at ``x`` on
        - ``trellis.led[x] = False`` turns the LED at ``x`` off
        - ``trellis.led.fill(bool)`` turns every LED on (True) or off (False)
        """
        self.led.fill(False)
        self._write_cmd(_HT16K33_OSCILATOR_ON)
        self.blink_rate = 0
        self.brightness = 15

    def _write_cmd(self, byte):
        self._temp[0] = byte
        for device in self._i2c_devices:
            with device:
                device.write(self._temp)

    @property
    def blink_rate(self):
        """
        The current blink rate as an integer range 0-3.
        """
        return self._blink_rate

    @blink_rate.setter
    def blink_rate(self, rate):
        if not 0 <= rate <= 3:
            raise ValueError("Blink rate must be an integer in the range: 0-3")
        rate = rate & 0x03
        self._blink_rate = rate
        self._write_cmd(_HT16K33_BLINK_CMD | _HT16K33_BLINK_DISPLAYON | rate << 1)

    @property
    def brightness(self):
        """
        The current brightness as an integer range 0-15.
        """
        return self._brightness

    @brightness.setter
    def brightness(self, brightness):
        if not 0 <= brightness <= 15:
            raise ValueError("Brightness must be an integer in the range: 0-15")
        brightness = brightness & 0x0F
        self._brightness = brightness
        self._write_cmd(_HT16K33_CMD_BRIGHTNESS | brightness)

    def show(self):
        """Refresh the LED buffer and show the changes."""
        pos = 0
        for device in self._i2c_devices:
            temp_led_buffer = bytearray(self._led_buffer[pos])
            with device:
                device.write(temp_led_buffer)
            pos += 1

    @property
    def auto_show(self):
        """
        Current state of sending LED updates directly the Trellis board(s). ``True``
        or ``False``.
        """
        return self._auto_show

    @auto_show.setter
    def auto_show(self, value):
        if value not in (True, False):
            raise ValueError("Auto show value must be True or False")
        self._auto_show = value

    def read_buttons(self):
        """
        Read the button matrix register on the Trellis board(s). Returns two
        lists: 1 for new button presses, 1 for button relases.
        """
        for i in range(len(self._buttons)):
            self._buttons[i][0] = bytearray(self._buttons[i][1])
        self._write_cmd(_HT16K33_KEY_READ_CMD)
        pos = 0
        for device in self._i2c_devices:
            with device:
                device.readinto(self._buttons[pos][1])
                pos += 1
        pressed = []
        released = []
        for i in range(self._num_leds):
            if self._just_pressed(i):
                pressed.append(i)
            elif self._just_released(i):
                released.append(i)

        return pressed, released

    def _is_pressed(self, button):
        mask = 1 << (buttonLUT[button % 16] & 0x0F)
        return self._buttons[button // 16][1][(buttonLUT[button % 16] >> 4)] & mask

    def _was_pressed(self, button):
        mask = 1 << (buttonLUT[button % 16] & 0x0F)
        return self._buttons[button // 16][0][(buttonLUT[button % 16] >> 4)] & mask

    def _just_pressed(self, button):
        # pylint: disable=invalid-unary-operand-type
        return self._is_pressed(button) & ~self._was_pressed(button)

    def _just_released(self, button):
        # pylint: disable=invalid-unary-operand-type
        return ~self._is_pressed(button) & self._was_pressed(button)
