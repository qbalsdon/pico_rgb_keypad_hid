import time
from constants import *
from adafruit_hid.keycode import Keycode

class DotAKeypadInterface():
    #--- OPTIONAL METHODS ---
    def dotaIntro(self):
        global image
        self.resetColours(COLOUR_OFF)

        for index in (10, 9, 5, 6, 7, 11, 15, 14, 13, 12, 8, 4, 0, 1, 2, 3):
            self.setKeyColour(index, self.IMAGE[index])
            time.sleep(0.05)
        time.sleep(0.25)

    #------------------------
    #----- PICO DISPLAY -----
    def getDisplaySettings(self):
        return ("dota", "images/dota.bmp")
    #------------------------
    #--- REQUIRED METHODS ---
    IMAGE = [
        COLOUR_WHITE, COLOUR_RED, COLOUR_RED, COLOUR_RED,
        COLOUR_RED, COLOUR_RED, COLOUR_WHITE, COLOUR_RED,
        COLOUR_RED, COLOUR_WHITE, COLOUR_RED, COLOUR_RED,
        COLOUR_RED, COLOUR_RED, COLOUR_RED, COLOUR_WHITE
    ]

    def getKeyColours(self):
        return (
            (darkVersion(self.IMAGE[0]),  COLOUR_CLEAR),
            (darkVersion(self.IMAGE[1]),  COLOUR_CLEAR),
            (darkVersion(self.IMAGE[2]),  COLOUR_CLEAR),
            (darkVersion(self.IMAGE[3]),  COLOUR_CLEAR),
            (darkVersion(self.IMAGE[4]),  COLOUR_CLEAR),
            (darkVersion(self.IMAGE[5]),  COLOUR_CLEAR),
            (darkVersion(self.IMAGE[6]),  COLOUR_CLEAR),
            (darkVersion(self.IMAGE[7]),  COLOUR_CLEAR),
            (darkVersion(self.IMAGE[8]),  COLOUR_CLEAR),
            (darkVersion(self.IMAGE[9]),  COLOUR_CLEAR),
            (darkVersion(self.IMAGE[10]), COLOUR_CLEAR),
            (darkVersion(self.IMAGE[11]), COLOUR_CLEAR),
            (darkVersion(self.IMAGE[12]), COLOUR_CLEAR),
            (darkVersion(self.IMAGE[13]), COLOUR_CLEAR),
            (darkVersion(self.IMAGE[14]), COLOUR_CLEAR),
            (darkVersion(self.IMAGE[15]), COLOUR_YELLOW)
        )

    def __init__(self, keyboard, keyboardLayout, setKeyColour):
        self.setKeyColour = setKeyColour
        self.keyboard = keyboard
        self.keyboardLayout= keyboardLayout

    def introduce(self):
        self.dotaIntro()
        self.resetColours(self.getKeyColours())
        time.sleep(0.2)

    def resetColours(self, colours):
        for key in range(BUTTON_COUNT):
            if len(colours) == 3:
                self.setKeyColour(key, colours)
            elif len(colours) == BUTTON_COUNT:
                self.setKeyColour(key, colours[key][0])

    def handleEvent(self, index, event):
        if not event & EVENT_SINGLE_PRESS:
            return

        if index == 0:
            self.keyboard.send(Keycode.Q)
        elif index == 1:
            self.keyboard.send(Keycode.W)
        elif index == 2:
            self.keyboard.send(Keycode.E)
        elif index == 3:
            self.keyboard.send(Keycode.R)
        elif index == 4:
            self.keyboard.send(Keycode.ONE)
        elif index == 5:
            self.keyboard.send(Keycode.TWO)
        elif index == 6:
            self.keyboard.send(Keycode.THREE)
        elif index == 7:
            self.keyboard.send(Keycode.T)
            time.sleep(0.01)
            self.keyboard.send(Keycode.T)
        elif index == 8:
            self.keyboard.send(Keycode.FOUR)
        elif index == 9:
            self.keyboard.send(Keycode.FIVE)
        elif index == 10:
            self.keyboard.send(Keycode.SIX)
        elif index == 11:
            self.keyboard.send(Keycode.F4) #Shop for now, Get next item and add to
        elif index == 12:
            self.keyboard.send(Keycode.F5) #QuickBuy
        elif index == 13:
            self.keyboard.send(Keycode.F1) #Focus Hero
        elif index == 14:
            self.keyboard.send(Keycode.F2) #Controlled Units
    #------------------------
