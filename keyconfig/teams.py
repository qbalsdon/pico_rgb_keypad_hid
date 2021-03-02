import time
from constants import *
from adafruit_hid.keycode import Keycode

class TeamsKeypad():
    #--- OPTIONAL METHODS ---

    def teamsIntro(self, frame):
        if frame >= 4:
            return
        for row in range(4):
            index = (frame * 4) + row
            self.setKeyColour(index, self.IMAGE[index])

    def teamsMicToggle(self):
        self.keyboard.send(Keycode.COMMAND, Keycode.SHIFT, Keycode.M)
    def teamsCameraToggle(self):
        self.keyboard.send(Keycode.COMMAND, Keycode.SHIFT, Keycode.O)
    def teamsHangUp(self):
        self.keyboard.send(Keycode.COMMAND, Keycode.SHIFT, Keycode.B)

    #------------------------
    #--- REQUIRED METHODS ---
    IMAGE = [
            COLOUR_WHITE, COLOUR_WHITE, COLOUR_WHITE, COLOUR_WHITE,
            COLOUR_WHITE, COLOUR_INDIGO, COLOUR_INDIGO, COLOUR_INDIGO,
            COLOUR_WHITE, COLOUR_WHITE, COLOUR_INDIGO, COLOUR_WHITE,
            COLOUR_WHITE, COLOUR_WHITE, COLOUR_INDIGO, COLOUR_WHITE
        ]

    def loop(self):
        if self.startAnimationTime > 0:
            estimatedFrame = int((timeInMillis() - self.startAnimationTime) / (ANIMATION_FRAME_MILLIS * 2))
            if estimatedFrame > self.currentFrame:
                # render new animation frame
                self.teamsIntro(self.frameIndex)
                self.frameIndex += 1
                # print("  ~~> Animation frame: ", estimatedFrame)
                self.currentFrame = estimatedFrame
                if self.frameIndex >= self.maxFrame:
                    self.startAnimationTime = -1

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
        self.resetColours(COLOUR_OFF)
        self.startAnimationTime = timeInMillis()
        self.currentFrame = -1
        self.maxFrame = 4
        self.frameIndex = 0

    def resetColours(self, colours):
        for key in range(BUTTON_COUNT):
            if isinstance(colours, int):
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
