# SPDX-FileCopyrightText: 2019 ladyada for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_pyoa`
================================================================================

A CircuitPython 'Choose Your Own Adventure' framework for PyPortal.


* Author(s): Adafruit

Implementation Notes
--------------------

**Hardware:**

* PyPortal
  https://www.adafruit.com/product/4116

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://github.com/adafruit/circuitpython/releases
"""

# pylint: disable=too-many-instance-attributes,no-self-use,line-too-long

# imports
import time
import json
import board
from digitalio import DigitalInOut
import displayio
import adafruit_touchscreen

try:  # No need for Cursor Control on the PyPortal
    from adafruit_cursorcontrol.cursorcontrol import Cursor
    from adafruit_cursorcontrol.cursorcontrol_cursormanager import CursorManager
except ImportError:
    pass
import audioio
from adafruit_display_text.label import Label
from adafruit_button import Button
import terminalio

__version__ = "2.2.3"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_PYOA.git"


class PYOA_Graphics:
    """A choose your own adventure game framework."""

    def __init__(self):
        self.root_group = displayio.Group(max_size=15)
        self._display = board.DISPLAY
        self._background_group = displayio.Group(max_size=1)
        self.root_group.append(self._background_group)
        self._text_group = displayio.Group(max_size=1)
        self.root_group.append(self._text_group)
        self._button_group = displayio.Group(max_size=2)
        self.root_group.append(self._button_group)

        if self._display.height > 250:
            self._text_group.scale = 2
            self._button_group.scale = 2

        self._speaker_enable = DigitalInOut(board.SPEAKER_ENABLE)
        self._speaker_enable.switch_to_output(False)
        if hasattr(board, "AUDIO_OUT"):
            self.audio = audioio.AudioOut(board.AUDIO_OUT)
        elif hasattr(board, "SPEAKER"):
            self.audio = audioio.AudioOut(board.SPEAKER)
        else:
            raise AttributeError("Board does not have an audio output!")

        self._background_file = None
        self._wavfile = None

        self._display.auto_brightness = False
        self.backlight_fade(0)
        self._display.show(self.root_group)
        self.touchscreen = None
        self.mouse_cursor = None
        if hasattr(board, "TOUCH_XL"):
            self.touchscreen = adafruit_touchscreen.Touchscreen(
                board.TOUCH_XL,
                board.TOUCH_XR,
                board.TOUCH_YD,
                board.TOUCH_YU,
                calibration=((5200, 59000), (5800, 57000)),
                size=(self._display.width, self._display.height),
            )
        elif hasattr(board, "BUTTON_CLOCK"):
            self.mouse_cursor = Cursor(
                self._display, display_group=self.root_group, cursor_speed=8
            )
            self.cursor = CursorManager(self.mouse_cursor)
        else:
            raise AttributeError("PYOA requires a touchscreen or cursor.")
        self._gamedirectory = None
        self._gamefilename = None
        self._game = None
        self._text = None
        self._background_sprite = None
        self._text_font = None
        self._left_button = None
        self._right_button = None
        self._middle_button = None

    def load_game(self, game_directory):
        """Load a game.

        :param game_directory: where the game files are stored
        """
        self._gamedirectory = game_directory
        self._text_font = terminalio.FONT
        # Possible Screen Sizes are:
        # 320x240 PyPortal and PyPortal Pynt
        # 160x128 PyBadge and PyGamer
        # 480x320 PyPortal Titano
        # 240x240 if we wanted to use HalloWing M4

        # Button Attributes
        btn_left = 10
        btn_right = btn_left + 180
        btn_mid = btn_left + 90
        button_y = 195
        button_width = 120
        button_height = 40
        if self._display.height < 200:
            button_y /= 2
            button_y += 10
            button_width /= 2
            button_height /= 2
            btn_right /= 2
            btn_mid /= 2
        elif self._display.height > 250:
            button_y *= 0.75
            button_y -= 20
            button_width *= 0.75
            button_height *= 0.75
            btn_right *= 0.75
            btn_mid *= 0.75
        self._left_button = Button(
            x=int(btn_left),
            y=int(button_y),
            width=int(button_width),
            height=int(button_height),
            label="Left",
            label_font=self._text_font,
            style=Button.SHADOWROUNDRECT,
        )
        self._right_button = Button(
            x=int(btn_right),
            y=int(button_y),
            width=int(button_width),
            height=int(button_height),
            label="Right",
            label_font=self._text_font,
            style=Button.SHADOWROUNDRECT,
        )
        self._middle_button = Button(
            x=int(btn_mid),
            y=int(button_y),
            width=int(button_width),
            height=int(button_height),
            label="Middle",
            label_font=self._text_font,
            style=Button.SHADOWROUNDRECT,
        )
        self._gamefilename = game_directory + "/cyoa.json"
        try:
            game_file = open(self._gamefilename, "r")
        except OSError as err:
            raise OSError("Could not open game file " + self._gamefilename) from err
        self._game = json.load(game_file)
        game_file.close()

    def _fade_to_black(self):
        """Turn down the lights."""
        if self.mouse_cursor:
            self.mouse_cursor.is_hidden = True
        self.backlight_fade(0)
        # turn off background so we can render the text
        self.set_background(None, with_fade=False)
        self.set_text(None, None)
        for _ in range(len(self._button_group)):
            self._button_group.pop()
        if self.mouse_cursor:
            self.mouse_cursor.is_hidden = False

    def _display_buttons(self, card):
        """Display the buttons of a card.

        :param card: The active card
        """
        button01_text = card.get("button01_text", None)
        button02_text = card.get("button02_text", None)
        self._left_button.label = button01_text
        self._middle_button.label = button01_text
        self._right_button.label = button02_text
        if button01_text and not button02_text:
            # show only middle button
            self._button_group.append(self._middle_button.group)
        if button01_text and button02_text:
            self._button_group.append(self._right_button.group)
            self._button_group.append(self._left_button.group)

    def _display_background_for(self, card):
        """If there's a background on card, display it.

        :param card: The active card
        """
        self.set_background(card.get("background_image", None), with_fade=False)

    def _display_text_for(self, card):
        """Display the main text of a card.

        :param card: The active card
        """
        text = card.get("text", None)
        text_color = card.get("text_color", 0x0)  # default to black
        if text:
            try:
                text_color = int(text_color)  # parse the JSON string to hex int
            except ValueError:
                text_color = 0x0
            self.set_text(text, text_color)

    def _play_sound_for(self, card):
        """If there's a sound, start playing it.

        :param card: The active card
        """
        sound = card.get("sound", None)
        loop = card.get("sound_repeat", False)
        if sound:
            loop = loop == "True"
            print("Loop:", loop)
            self.play_sound(sound, wait_to_finish=False, loop=loop)

    def _wait_for_press(self, card):
        """Wait for a button to be pressed.

        :param card: The active card

        Return the id of the destination card.
        """
        button01_text = card.get("button01_text", None)
        button02_text = card.get("button02_text", None)
        point_touched = None
        while True:
            if self.touchscreen is not None:
                point_touched = self.touchscreen.touch_point
            else:
                self.cursor.update()
                if self.cursor.is_clicked is True:
                    point_touched = self.mouse_cursor.x, self.mouse_cursor.y
            if point_touched is not None:
                point_touched = (
                    point_touched[0] // self._button_group.scale,
                    point_touched[1] // self._button_group.scale,
                )
                print("touch: ", point_touched)
                if button01_text and not button02_text:
                    # showing only middle button
                    if self._middle_button.contains(point_touched):
                        print("Middle button")
                        return card.get("button01_goto_card_id", None)
                if button01_text and button02_text:
                    if self._left_button.contains(point_touched):
                        print("Left button")
                        return card.get("button01_goto_card_id", None)
                    if self._right_button.contains(point_touched):
                        print("Right button")
                        return card.get("button02_goto_card_id", None)
            time.sleep(0.1)

    def display_card(self, card_num):
        """Display and handle input on a card.

        :param card_num: the index of the card to process
        """
        card = self._game[card_num]
        print(card)
        print("*" * 32)
        print("****{:^24s}****".format(card["card_id"]))
        print("*" * 32)

        self._fade_to_black()
        self._display_buttons(card)
        self._display_background_for(card)
        self.backlight_fade(1.0)
        self._display_text_for(card)
        try:
            self._display.refresh(target_frames_per_second=60)
        except AttributeError:
            self._display.refresh_soon()
            self._display.wait_for_frame()

        self._play_sound_for(card)

        auto_adv = card.get("auto_advance", None)
        if auto_adv is not None:
            auto_adv = float(auto_adv)
            print("Auto advancing after %0.1f seconds" % auto_adv)
            time.sleep(auto_adv)
            return card_num + 1

        destination_card_id = self._wait_for_press(card)

        self.play_sound(None)  # stop playing any sounds
        for card_number, card_struct in enumerate(self._game):
            if card_struct.get("card_id", None) == destination_card_id:
                return card_number  # found the matching card!
        # eep if we got here something went wrong
        raise RuntimeError(
            "Could not find card with matching 'card_id': ", destination_card_id
        )

    def play_sound(self, filename, *, wait_to_finish=True, loop=False):
        """Play a sound

        :param filename: The filename of the sound to play
        :param wait_to_finish: Whether playing the sound should block
        :param loop: Whether the sound should loop
        """
        self._speaker_enable.value = False
        self.audio.stop()
        if self._wavfile:
            self._wavfile.close()
            self._wavfile = None

        if not filename:
            return  # nothing more to do, just stopped
        filename = self._gamedirectory + "/" + filename
        print("Playing sound", filename)
        try:
            self._display.refresh(target_frames_per_second=60)
        except AttributeError:
            self._display.wait_for_frame()
        try:
            self._wavfile = open(filename, "rb")
        except OSError as err:
            raise OSError("Could not locate sound file", filename) from err

        wavedata = audioio.WaveFile(self._wavfile)
        self._speaker_enable.value = True
        self.audio.play(wavedata, loop=loop)
        if loop or not wait_to_finish:
            return
        while self.audio.playing:
            pass
        self._wavfile.close()
        self._wavfile = None
        self._speaker_enable.value = False

    def set_text(self, text, color):
        """Display the test for a card.

        :param text: the text to display
        :param color: the text color

        """
        if self._text_group:
            self._text_group.pop()
        if not text or not color:
            return  # nothing to do!
        text_wrap = 37
        if self._display.height < 130:
            text_wrap = 25
        text = self.wrap_nicely(text, text_wrap)
        text = "\n".join(text)
        print("Set text to", text, "with color", hex(color))
        text_x = 8
        text_y = 95
        if self._display.height < 130:
            text_x = 3
            text_y = 38
        elif self._display.height > 250:
            text_y = 50
        if text:
            self._text = Label(self._text_font, text=str(text))
            self._text.x = text_x
            self._text.y = text_y
            self._text.color = color
            self._text_group.append(self._text)

    def set_background(self, filename, *, with_fade=True):
        """The background image to a bitmap file.

        :param filename: The filename of the chosen background
        """
        print("Set background to", filename)
        if with_fade:
            self.backlight_fade(0)
        if self._background_group:
            self._background_group.pop()

        if filename:
            if self._background_file:
                self._background_file.close()
            self._background_file = open(self._gamedirectory + "/" + filename, "rb")
            background = displayio.OnDiskBitmap(self._background_file)
            self._background_sprite = displayio.TileGrid(
                background, pixel_shader=displayio.ColorConverter(), x=0, y=0
            )
            self._background_group.append(self._background_sprite)
        if with_fade:
            try:
                self._display.refresh(target_frames_per_second=60)
            except AttributeError:
                self._display.refresh_soon()
                self._display.wait_for_frame()
            self.backlight_fade(1.0)

    def backlight_fade(self, to_light):
        """Adjust the TFT backlight. Fade from one value to another"""
        from_light = self._display.brightness
        from_light = int(from_light * 100)
        to_light = max(0, min(1.0, to_light))
        to_light = int(to_light * 100)
        delta = 1
        if from_light > to_light:
            delta = -1
        for val in range(from_light, to_light, delta):
            self._display.brightness = val / 100
            time.sleep(0.003)
        self._display.brightness = to_light / 100

    # return a list of lines with wordwrapping
    # pylint: disable=invalid-name
    @staticmethod
    def wrap_nicely(string, max_chars):
        """A helper that will return a list of lines with word-break wrapping.

        :param str string: The text to be wrapped.
        :param int max_chars: The maximum number of characters on a line before wrapping.

        """
        # string = string.replace('\n', '').replace('\r', '') # strip confusing newlines
        words = string.split(" ")
        the_lines = []
        the_line = ""
        for w in words:
            if "\n" in w:
                w1, w2 = w.split("\n")
                the_line += " " + w1
                the_lines.append(the_line)
                the_line = w2
            elif len(the_line + " " + w) > max_chars:
                the_lines.append(the_line)
                the_line = "" + w
            else:
                the_line += " " + w
        if the_line:  # last line remaining
            the_lines.append(the_line)
        # remove first space from first line:
        the_lines[0] = the_lines[0][1:]
        return the_lines
