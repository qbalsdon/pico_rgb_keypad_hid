# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

import time
import displayio
from adafruit_gizmo import eink_gizmo

display = eink_gizmo.EInk_Gizmo()

# Create a display group for our screen objects
display_group = displayio.Group()

# Display a ruler graphic from the root directory of the CIRCUITPY drive
file = open("/display-ruler.bmp", "rb")

picture = displayio.OnDiskBitmap(file)
# Create a Tilegrid with the bitmap and put in the displayio group
sprite = displayio.TileGrid(picture, pixel_shader=displayio.ColorConverter())
display_group.append(sprite)

# Place the display group on the screen
display.show(display_group)

# Refresh the display to have it actually show the image
# NOTE: Do not refresh eInk displays sooner than 180 seconds
display.refresh()
print("refreshed")

time.sleep(180)
