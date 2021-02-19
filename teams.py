import time
from constants import *
from adafruit_hid.keycode import Keycode

class TeamsKeypadInterface():
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

    def __init__(self, keyboard, keyboardLayout, setKeyColour, resetState):
        self.setKeyColour = setKeyColour
        self.resetState = resetState
        self.keyboard = keyboard
        self.keyboardLayout= keyboardLayout

    def teamsIntro(self):
        self.resetState(COLOUR_OFF)

        for col in range(4):
            for row in range(4):
                index = (col * 4) + row
                self.setKeyColour(index, self.IMAGE[index])
            time.sleep(0.15)
        time.sleep(0.25)

    def introduce(self):
        self.teamsIntro()
        self.resetState(self.getKeyColours())
        time.sleep(0.2)

    def keyAction(self, index):
        if index == 0:
            self.teamsMicToggle()
        elif index == 1:
            self.teamsCameraToggle()
        elif index == 2:
            self.teamsHangUp()

    def teamsMicToggle(self):
        self.keyboard.send(Keycode.COMMAND, Keycode.SHIFT, Keycode.M)
    def teamsCameraToggle(self):
        self.keyboard.send(Keycode.COMMAND, Keycode.SHIFT, Keycode.O)
    def teamsHangUp(self):
        self.keyboard.send(Keycode.COMMAND, Keycode.SHIFT, Keycode.B)
