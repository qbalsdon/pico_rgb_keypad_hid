"""
SOURCES:
 - http://helloraspberrypi.blogspot.com/2021/01/raspberry-pi-picocircuitpython-st7789.html
 - https://learn.adafruit.com/circuitpython-display-support-using-displayio

Example of CircuitPython/RaspberryPi Pico
to display on 1.14" 135x240 (RGB) IPS screen
with ST7789 driver via SPI interface.

Connection between Pico and
the IPS screen, with ST7789 SPI interface.
GP21 - CS
GP20 - DC
GP22 - RES --> REALLY want this in "Run"
GP26 - SDA
GP27 - SCL
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
from pwmio import PWMOut

from digitalio import DigitalInOut, Direction, Pull

from constants import *

# REMEMBER THIS ONE IF YOU WIRE UP THE OTHER BUTTONS!!
DISPLAY_BUTTON_COUNT = 2

PWM_FREQ  = 5000
DIM_VALUE = 65535

class PicoDisplay():
    def __init__(self, GPIO_RESET     = None,
                       GPIO_MOSI      = board.GP27,
                       GPIO_CLK       = board.GP26,
                       GPIO_CS        = board.GP21,
                       GPIO_DC        = board.GP20,
                       GPIO_BL        = board.GP22,
                       DISPLAY_WIDTH  = 135,
                       DISPLAY_HEIGHT = 240,
                       xButtonPin     = board.GP14,
                       yButtonPin     = board.GP15,
                       aButtonPin     = None, #board.GP14,
                       bButtonPin     = None): #board.GP15):
        # Release any resources currently in use for the displays
        displayio.release_displays()
                                   # COLOUR     ORIGINAL TYPE
        self.tft_res  = GPIO_RESET # BROWN      GP--     RESET
        self.spi_mosi = GPIO_MOSI  # ORANGE     GP19     SCL
        self.spi_clk  = GPIO_CLK   # YELLOW     GP18     SDA
        self.tft_cs   = GPIO_CS    # GREEN      GP17     CS
        self.tft_dc   = GPIO_DC    # BLUE       GP16     DC


        self.spi = busio.SPI(self.spi_clk, MOSI=self.spi_mosi)

        self.display_bus = displayio.FourWire(
            self.spi, command=self.tft_dc, chip_select=self.tft_cs, reset=self.tft_res
        )
        self.SCREEN_WIDTH = DISPLAY_WIDTH
        self.SCREEN_HEIGHT = DISPLAY_HEIGHT

        self.display = adafruit_st7789.ST7789(self.display_bus,
                            width=DISPLAY_WIDTH,
                            height=DISPLAY_HEIGHT,
                            rowstart=40, colstart=53)
        if GPIO_BL != None:
            self.backLight = PWMOut(GPIO_BL, frequency=PWM_FREQ, duty_cycle = DIM_VALUE)
        self.Buttons = []
        if xButtonPin != None:
            self.xButton = DigitalInOut(xButtonPin)
            self.xButton.direction = Direction.INPUT
            self.xButton.pull = Pull.UP
            self.Buttons.append(self.xButton)
        if yButtonPin != None:
            self.yButton = DigitalInOut(yButtonPin)
            self.yButton.direction = Direction.INPUT
            self.yButton.pull = Pull.UP
            self.Buttons.append(self.yButton)
        if aButtonPin != None:
            self.aButton = DigitalInOut(aButtonPin)
            self.aButton.direction = Direction.INPUT
            self.aButton.pull = Pull.UP
            self.Buttons.append(self.aButton)
        if bButtonPin != None:
            self.bButton = DigitalInOut(bButtonPin)
            self.bButton.direction = Direction.INPUT
            self.bButton.pull = Pull.UP
            self.Buttons.append(self.bButton)

        if len(self.Buttons) > 0:
            self.TimeDown = [-1] * DISPLAY_BUTTON_COUNT
            self.TimeUp = [-1] * DISPLAY_BUTTON_COUNT
            self.Waiting = [False] * DISPLAY_BUTTON_COUNT
            self.ButtonStates = [ self.TimeDown, self.TimeUp, self.Waiting ]

    def printInfo():
        print("==============================")
        print(os.uname())
        print(" -- Raspberry Pi Pico/CircuitPython ST7789 SPI IPS Display -- ")
        print(" -- " + adafruit_st7789.__name__ + " version: " + adafruit_st7789.__version__ + " -- ")
        print("==============================")

    def convertScale(self, value, originMin=0, originMax=100, destinationMin=0, destinationMax=DIM_VALUE):
        originSpan = originMax - originMin
        destinationSpan = destinationMax - destinationMin
        scaledValue = float(value - originMin) / float(originSpan)
        return destinationMin + (scaledValue * destinationSpan)

    def setBacklightPercent(self, percent):
        if self.backLight != None:
            self.backLight.duty_cycle = int(self.convertScale(percent))

    def createPalette(self, colour):
        palette = displayio.Palette(1)
        palette[0] = colour
        return palette

    def getImage(self, fileReference, imagePalette=None, top=0, right=0):
        bitmap, palette = adafruit_imageload.load(fileReference,
                                             bitmap=displayio.Bitmap,
                                             palette=displayio.Palette)
        if imagePalette is None:
            imagePalette = palette
        # Create a TileGrid to hold the bitmap
        tile_grid = displayio.TileGrid(bitmap, pixel_shader=imagePalette)

        # Create a Group to hold the TileGrid
        group = displayio.Group(x=top, y=right)

        # Add the TileGrid to the Group
        group.append(tile_grid)
        return group

    def createGroup(self, max=10):
        return displayio.Group(max_size=max)

    def simpleRectangle(self, width, height):
        rect = displayio.Bitmap(height, width, 1) # I have swapped order because that's how I think
        return rect

    def createTileGrid(self, top, right, rectangle, colour,):
        palette = displayio.Palette(1)
        palette[0] = colour
        return displayio.TileGrid(rectangle, pixel_shader=palette, x=top, y=right)

    def createRectangle(self, top, right, width, height, colour):
        rect = displayio.Bitmap(height, width, 1) # I have swapped order because that's how I think
        palette = displayio.Palette(1)
        palette[0] = colour
        return displayio.TileGrid(rect, pixel_shader=palette, x=top, y=right)


    def render(self, spriteGroup, rotation):
        self.display.rotation = rotation
        self.display.show(spriteGroup)

    def createText(self, displayText, fontColour, xCoord, yCoord):
        text_group = displayio.Group(max_size=12, scale=4, x=xCoord, y=yCoord)
        text_group.append(label.Label(terminalio.FONT, text=displayText, color=fontColour))
        return text_group

    # ------------ Custom Wallpapers ------------

    def createRainbow(self):
        size = int(self.SCREEN_WIDTH / len(RAINBOW))
        box = self.createGroup()
        for index in range(len(RAINBOW)):
            box.append(self.createRectangle(0, index * size,size, self.SCREEN_HEIGHT, RAINBOW[index]))
        return box

    def getAndroid(self):
        group = self.createGroup()
        backgroundColour = COLOUR_ANDROID_BLUE

        palette = displayio.Palette(3)
        palette[0] = backgroundColour
        palette[1] = COLOUR_ANDROID_GREEN
        palette[2] = COLOUR_WHITE
        image = self.getImage("images/android.bmp", palette, 0, 20)

        backdrop = self.createRectangle(0, 0, self.SCREEN_WIDTH, self.SCREEN_HEIGHT, backgroundColour)

        group.append(backdrop)
        group.append(image)
        group.append(self.createText("Android", COLOUR_WHITE, 60, 40))
        return group

    def getTeams(self):
        group = self.createGroup()
        backgroundColour = COLOUR_TEAMS

        palette = displayio.Palette(2)
        palette[0] = backgroundColour
        palette[1] = COLOUR_WHITE
        image = self.getImage("images/teams.bmp", palette, 0, 10)

        backdrop = self.createRectangle(0, 0, self.SCREEN_WIDTH, self.SCREEN_HEIGHT, backgroundColour)

        group.append(backdrop)
        group.append(image)
        group.append(self.createText("Teams", COLOUR_WHITE, 115, 60))
        return group

    def getMidi(self):
        group = self.createGroup()

        palette = displayio.Palette(8)
        palette[0] = COLOUR_WHITE
        palette[1] = COLOUR_VIOLET
        palette[2] = COLOUR_BLUE
        palette[3] = COLOUR_RED
        palette[4] = COLOUR_ORANGE
        palette[5] = COLOUR_GREEN
        palette[6] = COLOUR_YELLOW
        palette[7] = COLOUR_BLACK
        image = self.getImage("images/midi.bmp", palette, 0, 0)

        group.append(image)
        return group

    def getDota(self):
        group = self.createGroup()
        foregroundColour = COLOUR_DOTA

        palette = displayio.Palette(2)
        palette[0] = COLOUR_BLACK
        palette[1] = foregroundColour
        image = self.getImage("images/dota.bmp", palette, self.SCREEN_WIDTH - 10, 20)

        backdrop = self.createRectangle(0, 0, self.SCREEN_WIDTH, self.SCREEN_HEIGHT, COLOUR_BLACK)

        group.append(backdrop)
        group.append(image)
        group.append(self.createText("Dota", foregroundColour, 5, 100))
        return group
    # -------------------------------------------

    # settings is currently a tuple: (text, fileReference), where
    #   text           : a string that will be displayed in BLUE
    #   fileReference  : a string indicating the location of an
    #                    INDEXED Bitmap file
    def displayMode(self, settings):
        self.display.rotation = 270

        splash = displayio.Group(max_size=10)
        self.display.show(splash)

        # BACKGROUND
        color_bitmap = displayio.Bitmap(self.SCREEN_WIDTH, SCREEN_HEIGHT, 1) # HEIGHT, WIDTH swapped because we're rotated
        color_palette = displayio.Palette(1)
        color_palette[0] = COLOUR_BLACK
        bg_sprite = displayio.TileGrid(color_bitmap,
                                       pixel_shader=color_palette, x=0, y=0)

        # TITLE
        text_group = displayio.Group(max_size=12, scale=4, x=60, y=40)
        text1 = settings[0]
        text_area = label.Label(terminalio.FONT, text=text1, color=COLOUR_WHITE)
        text_group.append(text_area)  # Subgroup for text scaling

        # PUT IT ALL ON THE SCREEN
        splash.append(bg_sprite)
        splash.append(self.getImage(settings[1]))
        splash.append(text_group)

    def displayScreen(self):
        # Make the display context
        splash = displayio.Group(max_size=10)
        self.display.show(splash)

        color_bitmap = displayio.Bitmap(240, 240, 1)
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
