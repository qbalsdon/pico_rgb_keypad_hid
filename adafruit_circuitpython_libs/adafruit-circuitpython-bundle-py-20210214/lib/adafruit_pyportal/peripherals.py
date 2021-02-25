# SPDX-FileCopyrightText: 2017 Scott Shawcroft, written for Adafruit Industries
# SPDX-FileCopyrightText: Copyright (c) 2020 Melissa LeBlanc-Williams for Adafruit Industries
#
# SPDX-License-Identifier: MIT
"""
`adafruit_pyportal.peripherals`
================================================================================

CircuitPython driver for Adafruit PyPortal.

* Author(s): Limor Fried, Kevin J. Walters, Melissa LeBlanc-Williams

Implementation Notes
--------------------

**Hardware:**

* `Adafruit PyPortal <https://www.adafruit.com/product/4116>`_

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://github.com/adafruit/circuitpython/releases

"""

import gc
import board
from digitalio import DigitalInOut
import pwmio
import audioio
import audiocore
import storage

try:
    import sdcardio

    NATIVE_SD = True
except ImportError:
    import adafruit_sdcard as sdcardio

    NATIVE_SD = False

__version__ = "5.1.3"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_PyPortal.git"


class Peripherals:
    """Peripherals Helper Class for the PyPortal Library"""

    # pylint: disable=too-many-instance-attributes, too-many-locals, too-many-branches, too-many-statements
    def __init__(self, spi, display, splash_group, debug=False):
        # Speaker Enable
        self._speaker_enable = DigitalInOut(board.SPEAKER_ENABLE)
        self._speaker_enable.switch_to_output(False)

        self._display = display

        if hasattr(board, "AUDIO_OUT"):
            self.audio = audioio.AudioOut(board.AUDIO_OUT)
        elif hasattr(board, "SPEAKER"):
            self.audio = audioio.AudioOut(board.SPEAKER)
        else:
            raise AttributeError("Board does not have a builtin speaker!")

        if debug:
            print("Init SD Card")
        sd_cs = board.SD_CS
        if not NATIVE_SD:
            sd_cs = DigitalInOut(sd_cs)
        self._sdcard = None

        try:
            self._sdcard = sdcardio.SDCard(spi, sd_cs)
            vfs = storage.VfsFat(self._sdcard)
            storage.mount(vfs, "/sd")
        except OSError as error:
            print("No SD card found:", error)

        try:
            if hasattr(board, "TFT_BACKLIGHT"):
                self._backlight = pwmio.PWMOut(
                    board.TFT_BACKLIGHT
                )  # pylint: disable=no-member
            elif hasattr(board, "TFT_LITE"):
                self._backlight = pwmio.PWMOut(
                    board.TFT_LITE
                )  # pylint: disable=no-member
        except ValueError:
            self._backlight = None
        self.set_backlight(1.0)  # turn on backlight
        # pylint: disable=import-outside-toplevel
        if hasattr(board, "TOUCH_XL"):
            import adafruit_touchscreen

            if debug:
                print("Init touchscreen")
            # pylint: disable=no-member
            self.touchscreen = adafruit_touchscreen.Touchscreen(
                board.TOUCH_XL,
                board.TOUCH_XR,
                board.TOUCH_YD,
                board.TOUCH_YU,
                calibration=((5200, 59000), (5800, 57000)),
                size=(board.DISPLAY.width, board.DISPLAY.height),
            )
            # pylint: enable=no-member

            self.set_backlight(1.0)  # turn on backlight
        elif hasattr(board, "BUTTON_CLOCK"):
            from adafruit_cursorcontrol.cursorcontrol import Cursor
            from adafruit_cursorcontrol.cursorcontrol_cursormanager import CursorManager

            if debug:
                print("Init cursor")
            self.mouse_cursor = Cursor(
                board.DISPLAY, display_group=splash_group, cursor_speed=8
            )
            self.mouse_cursor.hide()
            self.cursor = CursorManager(self.mouse_cursor)
        else:
            raise AttributeError(
                "PyPortal module requires either a touchscreen or gamepad."
            )
        # pylint: enable=import-outside-toplevel

        gc.collect()

    def set_backlight(self, val):
        """Adjust the TFT backlight.

        :param val: The backlight brightness. Use a value between ``0`` and ``1``, where ``0`` is
                    off, and ``1`` is 100% brightness.

        """
        val = max(0, min(1.0, val))
        if self._backlight:
            self._backlight.duty_cycle = int(val * 65535)
        else:
            self._display.auto_brightness = False
            self._display.brightness = val

    def play_file(self, file_name, wait_to_finish=True):
        """Play a wav file.

        :param str file_name: The name of the wav file to play on the speaker.

        """
        wavfile = open(file_name, "rb")
        wavedata = audiocore.WaveFile(wavfile)
        self._speaker_enable.value = True
        self.audio.play(wavedata)
        if not wait_to_finish:
            return
        while self.audio.playing:
            pass
        wavfile.close()
        self._speaker_enable.value = False

    def sd_check(self):
        """Returns True if there is an SD card preset and False
        if there is no SD card. The _sdcard value is set in _init
        """
        if self._sdcard:
            return True
        return False

    @property
    def speaker_disable(self):
        """
        Enable or disable the speaker for power savings
        """
        return not self._speaker_enable.value

    @speaker_disable.setter
    def speaker_disable(self, value):
        self._speaker_enable.value = not value
