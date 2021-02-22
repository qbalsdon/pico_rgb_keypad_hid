import time
from constants import *
from adafruit_hid.keycode import Keycode

class TeamsKeypadInterface():
    #--- OPTIONAL METHODS ---
    def teamsIntro(self):
        self.resetColours(COLOUR_OFF)

        for col in range(4):
            for row in range(4):
                index = (col * 4) + row
                self.setKeyColour(index, self.IMAGE[index])
            time.sleep(0.15)
        time.sleep(0.25)

    def teamsMicToggle(self):
        self.keyboard.send(Keycode.COMMAND, Keycode.SHIFT, Keycode.M)
    def teamsCameraToggle(self):
        self.keyboard.send(Keycode.COMMAND, Keycode.SHIFT, Keycode.O)
    def teamsHangUp(self):
        self.keyboard.send(Keycode.COMMAND, Keycode.SHIFT, Keycode.B)

    #------------------------
    #----- PICO DISPLAY -----
    def getDisplaySettings(self):
        return ("teams", "images/teams.bmp")
    #------------------------
    #--- REQUIRED METHODS ---
    IMAGE = [
            COLOUR_WHITE, COLOUR_WHITE, COLOUR_WHITE, COLOUR_WHITE,
            COLOUR_WHITE, COLOUR_INDIGO, COLOUR_INDIGO, COLOUR_INDIGO,
            COLOUR_WHITE, COLOUR_WHITE, COLOUR_INDIGO, COLOUR_WHITE,
            COLOUR_WHITE, COLOUR_WHITE, COLOUR_INDIGO, COLOUR_WHITE
        ]

    def getKeyColours(self):
        return (
            (darkVersion(self.IMAGE[0]),  COLOUR_ORANGE),
            (darkVersion(self.IMAGE[1]),  COLOUR_BLUE),
            (darkVersion(self.IMAGE[2]),  COLOUR_RED),
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
        self.teamsIntro()
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
            self.teamsMicToggle()
        elif index == 1:
            self.teamsCameraToggle()
        elif index == 2:
            self.teamsHangUp()
    #------------------------
