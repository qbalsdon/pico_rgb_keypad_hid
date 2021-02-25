# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

"""Simple test script for 4.2" 400x300 black and white displays.

Supported products:
  * WaveShare 4.2" Black and White
    * https://www.waveshare.com/product/modules/oleds-lcds/e-paper/4.2inch-e-paper.htm
    * https://www.waveshare.com/product/modules/oleds-lcds/e-paper/4.2inch-e-paper-module.htm
  """

import time
import board
import displayio
import adafruit_il0398

displayio.release_displays()

# This pinout works on a Feather M4 and may need to be altered for other boards.
spi = board.SPI()  # Uses SCK and MOSI
epd_cs = board.D9
epd_dc = board.D10
epd_reset = board.D5
epd_busy = board.D6

display_bus = displayio.FourWire(
    spi, command=epd_dc, chip_select=epd_cs, reset=epd_reset, baudrate=1000000
)
time.sleep(1)

display = adafruit_il0398.IL0398(
    display_bus, width=400, height=300, seconds_per_frame=20, busy_pin=epd_busy
)

g = displayio.Group()

f = open("/display-ruler.bmp", "rb")

pic = displayio.OnDiskBitmap(f)
t = displayio.TileGrid(pic, pixel_shader=displayio.ColorConverter())
g.append(t)

display.show(g)

display.refresh()

time.sleep(120)
