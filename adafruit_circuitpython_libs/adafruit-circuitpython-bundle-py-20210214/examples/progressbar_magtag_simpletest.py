# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

"""
Basic progressbar example script
adapted for use on MagTag.
"""
import time
import board
import displayio
import digitalio
from adafruit_progressbar import ProgressBar

# use built in display (PyPortal, PyGamer, PyBadge, CLUE, etc.)
# see guide for setting up external displays (TFT / OLED breakouts, RGB matrices, etc.)
# https://learn.adafruit.com/circuitpython-display-support-using-displayio/display-and-display-bus
display = board.DISPLAY
time.sleep(display.time_to_refresh)

# a button will be used to advance the progress
a_btn = digitalio.DigitalInOut(board.BUTTON_A)
a_btn.direction = digitalio.Direction.INPUT
a_btn.pull = digitalio.Pull.UP

# Make the display context
splash = displayio.Group(max_size=10)
display.show(splash)

# set progress bar width and height relative to board's display
BAR_WIDTH = display.width - 40
BAR_HEIGHT = 30

x = display.width // 2 - BAR_WIDTH // 2
y = display.height // 3

# Create a new progress_bar object at (x, y)
progress_bar = ProgressBar(
    x, y, BAR_WIDTH, BAR_HEIGHT, 1.0, bar_color=0x666666, outline_color=0xFFFFFF
)

# Append progress_bar to the splash group
splash.append(progress_bar)

current_progress = (time.monotonic() % 101) / 100.0
print(current_progress)
progress_bar.progress = current_progress

# refresh the display
display.refresh()

prev_a = a_btn.value
while True:
    cur_a = a_btn.value
    # if a_btn was just pressed down
    if not cur_a and prev_a:
        current_progress += 0.20
        if current_progress > 1.0:
            current_progress = 0.0
        print(current_progress)
        progress_bar.progress = current_progress

        time.sleep(display.time_to_refresh)
        display.refresh()
        time.sleep(display.time_to_refresh)

    prev_a = cur_a
