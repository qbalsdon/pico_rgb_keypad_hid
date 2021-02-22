"""
SOURCES:
 - http://helloraspberrypi.blogspot.com/2021/01/raspberry-pi-picocircuitpython-st7789.html
 - https://learn.adafruit.com/circuitpython-display-support-using-displayio

Example of CircuitPython/RaspberryPi Pico
to display on 1.14" 135x240 (RGB) IPS screen
with ST7789 driver via SPI interface.

Connection between Pico and
the IPS screen, with ST7789 SPI interface.
3V3  - BLK (backlight, always on)
GP11 - CS
GP12 - DC
GP13 - RES
GP15 - SDA
GP14 - SCL
3V3  - VCC
GND  - GND
"""

import os
import board
import time
import terminalio
import displayio
import busio
from adafruit_display_text import label
import adafruit_imageload
import adafruit_st7789

print("==============================")
print(os.uname())
print("Hello Raspberry Pi Pico/CircuitPython ST7789 SPI IPS Display")
print(adafruit_st7789.__name__ + " version: " + adafruit_st7789.__version__)
print()

# Release any resources currently in use for the displays
displayio.release_displays()

# TODO: BUTTONS
#A 12
#B 13
#X 14
#Y 15
                      # COLOUR     ORIGINAL TYPE
tft_res = board.GP22  # BROWN      GP11
spi_mosi = board.GP27 # ORANGE     GP15
spi_clk = board.GP26  # YELLOW     GP14
tft_cs = board.GP21   # GREEN      GP13     SCL
tft_dc = board.GP20   # BLUE       GP12     SDA

# IN USE:
# 5  - 3
# 6  - 4
# 7  - 5
# 25 - 19
# 24 - 18
# 22 - 17

"""
classbusio.SPI(clock: microcontroller.Pin,
                MOSI: Optional[microcontroller.Pin] = None,
                MISO: Optional[microcontroller.Pin] = None)
"""
spi = busio.SPI(spi_clk, MOSI=spi_mosi)

display_bus = displayio.FourWire(
    spi, command=tft_dc, chip_select=tft_cs, reset=tft_res
)

display = adafruit_st7789.ST7789(display_bus,
                    width=135, height=240,
                    rowstart=40, colstart=53)

def getImage(fileReference):
    bitmap, palette = adafruit_imageload.load(fileReference,
                                         bitmap=displayio.Bitmap,
                                         palette=displayio.Palette)
    # Create a TileGrid to hold the bitmap
    tile_grid = displayio.TileGrid(bitmap, pixel_shader=palette)

    # Create a Group to hold the TileGrid
    group = displayio.Group()

    # Add the TileGrid to the Group
    group.append(tile_grid)
    return group

# settings is currently a tuple: (text, fileReference), where
#   text           : a string that will be displayed in BLUE
#   fileReference  : a string indicating the location of an
#                    INDEXED Bitmap file
def displayMode(settings):
    display.rotation = 270
    SCREEN_WIDTH = 240
    SCREEN_HEIGHT = 135

    GREEN=0x44de97
    BLUE=0x013f54
    WHITE=0xFFFFFF
    BLACK=0x000000
    splash = displayio.Group(max_size=10)
    display.show(splash)

    # BACKGROUND
    color_bitmap = displayio.Bitmap(SCREEN_WIDTH, SCREEN_HEIGHT, 1) # HEIGHT, WIDTH swapped because we're rotated
    color_palette = displayio.Palette(1)
    color_palette[0] = BLACK
    bg_sprite = displayio.TileGrid(color_bitmap,
                                   pixel_shader=color_palette, x=0, y=0)

    # TITLE
    text_group = displayio.Group(max_size=12, scale=4, x=60, y=40)
    text1 = settings[0]
    text_area = label.Label(terminalio.FONT, text=text1, color=WHITE)
    text_group.append(text_area)  # Subgroup for text scaling

    # PUT IT ALL ON THE SCREEN
    splash.append(bg_sprite)
    splash.append(getImage(settings[1]))
    splash.append(text_group)

    #splash.append(bg_sprite)
    #splash.append(text_group)

def displayScreen():
    # Make the display context
    splash = displayio.Group(max_size=10)
    display.show(splash)

    color_bitmap = displayio.Bitmap(135, 240, 1)
    color_palette = displayio.Palette(1)
    color_palette[0] = 0x00FF00

    bg_sprite = displayio.TileGrid(color_bitmap,
                                   pixel_shader=color_palette, x=0, y=0)
    splash.append(bg_sprite)

    # Draw a smaller inner rectangle
    inner_bitmap = displayio.Bitmap(133, 238, 1)
    inner_palette = displayio.Palette(1)
    inner_palette[0] = 0x0000FF
    inner_sprite = displayio.TileGrid(inner_bitmap,
                                      pixel_shader=inner_palette, x=1, y=1)
    splash.append(inner_sprite)

    # Draw a label
    text_group1 = displayio.Group(max_size=10, scale=2, x=20, y=40)
    text1 = "RPi Pico"
    text_area1 = label.Label(terminalio.FONT, text=text1, color=0xFF0000)
    text_group1.append(text_area1)  # Subgroup for text scaling
    # Draw a label
    text_group2 = displayio.Group(max_size=10, scale=1, x=20, y=60)
    text2 = "CircuitPython"
    text_area2 = label.Label(terminalio.FONT, text=text2, color=0xFFFFFF)
    text_group2.append(text_area2)  # Subgroup for text scaling

    # Draw a label
    text_group3 = displayio.Group(max_size=10, scale=1, x=20, y=100)
    text3 = adafruit_st7789.__name__
    text_area3 = label.Label(terminalio.FONT, text=text3, color=0x0000000)
    text_group3.append(text_area3)  # Subgroup for text scaling
    # Draw a label
    text_group4 = displayio.Group(max_size=10, scale=2, x=20, y=120)
    text4 = adafruit_st7789.__version__
    text_area4 = label.Label(terminalio.FONT, text=text4, color=0x000000)
    text_group4.append(text_area4)  # Subgroup for text scaling

    splash.append(text_group1)
    splash.append(text_group2)
    splash.append(text_group3)
    splash.append(text_group4)
