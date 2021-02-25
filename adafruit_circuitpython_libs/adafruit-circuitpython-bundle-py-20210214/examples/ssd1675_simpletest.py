# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

"""Simple test script for 2.13" 250x122 black and white featherwing.

Supported products:
  * Adafruit 2.13" Black and White FeatherWing
    * https://www.adafruit.com/product/4195
  """

import time
import board
import displayio
import adafruit_ssd1675

displayio.release_displays()

epd_cs = board.D9
epd_dc = board.D10

display_bus = displayio.FourWire(
    board.SPI(), command=epd_dc, chip_select=epd_cs, baudrate=1000000
)
time.sleep(1)

display = adafruit_ssd1675.SSD1675(display_bus, width=250, height=122, rotation=90)

g = displayio.Group()

f = open("/display-ruler.bmp", "rb")

pic = displayio.OnDiskBitmap(f)
t = displayio.TileGrid(pic, pixel_shader=displayio.ColorConverter())
g.append(t)

display.show(g)

display.refresh()

print("refreshed")

time.sleep(120)
