import time
from constants import *

RAINBOW = [COLOUR_RED, COLOUR_ORANGE, COLOUR_YELLOW, COLOUR_GREEN, COLOUR_BLUE, COLOUR_INDIGO, COLOUR_VIOLET]

class KeypadInterface():
    #--- OPTIONAL METHODS ---
    def tasteTheRainbow(self, index):
        DIAG = [[0],[1,4],[2,5,8],[3,6,9,12],[7,10,13],[11,14],[15]]
        currentColourIndex = 0
        for snakeIndex in range(index - (len(RAINBOW)), index):
            if snakeIndex >=0:
                currentIndex = snakeIndex % len(DIAG)
                currentDiag = DIAG[currentIndex]
                currentColour = RAINBOW[currentColourIndex]
                for button in currentDiag:
                    self.setKeyColour(button, currentColour)
                currentIndex-=1
                currentColourIndex+=1
    #------------------------
    #--- REQUIRED METHODS ---

    # defines the 'default' and 'pressed' states of the keys
    def getKeyColours(self):
        return (
            (COLOUR_RED, COLOUR_WHITE),
            (COLOUR_ORANGE, COLOUR_WHITE),
            (COLOUR_YELLOW, COLOUR_WHITE),
            (COLOUR_GREEN, COLOUR_WHITE),
            (COLOUR_ORANGE, COLOUR_WHITE),
            (COLOUR_YELLOW, COLOUR_WHITE),
            (COLOUR_GREEN, COLOUR_WHITE),
            (COLOUR_BLUE, COLOUR_WHITE),
            (COLOUR_YELLOW, COLOUR_WHITE),
            (COLOUR_GREEN, COLOUR_WHITE),
            (COLOUR_BLUE, COLOUR_WHITE),
            (COLOUR_INDIGO, COLOUR_WHITE),
            (COLOUR_GREEN, COLOUR_WHITE),
            (COLOUR_BLUE, COLOUR_WHITE),
            (COLOUR_INDIGO, COLOUR_WHITE),
            (COLOUR_VIOLET, COLOUR_WHITE)
        )

    def loop(self):
        if self.startAnimationTime > 0:
            estimatedFrame = int((timeInMillis() - self.startAnimationTime) / ANIMATION_FRAME_MILLIS)
            if estimatedFrame > self.currentFrame:
                # render new animation frame
                self.tasteTheRainbow(estimatedFrame)
                # print("  ~~> Animation frame: ", estimatedFrame)
                self.currentFrame = estimatedFrame
                if self.currentFrame >= self.maxFrame:
                    self.startAnimationTime = -1
                    self.resetColours(self.getKeyColours())

    def __init__(self, keyboard, keyboardLayout, setKeyColour):
        self.setKeyColour = setKeyColour
        self.keyboard = keyboard
        self.keyboardLayout= keyboardLayout
        self.startAnimationTime = -1

    # does the animation for the keys
    def introduce(self, loops = 5):
        self.startAnimationTime = timeInMillis()
        self.currentFrame = -1
        self.maxFrame = (loops + 1) * len(RAINBOW)

    # sets the colours of the keys back to the resting state
    def resetColours(self, colours):
        for key in range(BUTTON_COUNT):
            if len(colours) == 3:
                self.setKeyColour(key, colours)
            elif len(colours) == BUTTON_COUNT:
                self.setKeyColour(key, colours[key][0])

    # get the help message for a particular key
    # index - the key index [0-15]
    # event - one of the defined event types [optional]
    def helpForKey(self, index, event = None):
        self.help = (
            ("Press event","Double Press Event","Hold Event","Long Hold Event"),
        )
        if event == None:
            return self.help[0]
        else:
            button = 0
            if event & EVENT_SINGLE_PRESS:
                return self.help[button][0]
            elif event & EVENT_DOUBLE_PRESS:
                return self.help[button][1]
            elif event & EVENT_LONG_PRESS:
                return self.help[button][2]
            elif event & EVENT_EXTRA_LONG_PRESS:
                return self.help[button][3]

    # defines the behvaiour of each key
    #    keyIndex: [0-15] which key has had an event
    #    event:    what type of event occurred.
    #              Be aware that EVENT_KEY_UP and
    #              EVENT_KEY_DOWN can occur several
    #              times in one action.
    #              Can be a combination of:
    #                - EVENT_SINGLE_PRESS
    #                - EVENT_DOUBLE_PRESS
    #                - EVENT_LONG_PRESS
    #                - EVENT_EXTRA_LONG_PRESS
    #                - EVENT_KEY_UP
    #                - EVENT_KEY_DOWN
    def handleEvent(self, keyIndex, event):
        if event & EVENT_SINGLE_PRESS:
            print("  ~~> [", keyIndex, "] single press")
            self.introduce(keyIndex)
            self.resetColours(self.getKeyColours())
        elif event & EVENT_DOUBLE_PRESS:
            print("  ~~> [", keyIndex, "] double press")
        elif event & EVENT_LONG_PRESS:
            print("  ~~> [", keyIndex, "] long press")
        elif event & EVENT_EXTRA_LONG_PRESS:
            print("  ~~> [", keyIndex, "] extra long press")
        if event & EVENT_KEY_UP:
            print("    ~~> [", keyIndex, "] key up")
        if event & EVENT_KEY_DOWN:
            print("    ~~> [", keyIndex, "] key down")
    #------------------------
