import time
from constants import *

class KeypadInterface():
    #--- OPTIONAL METHODS ---
    def tasteTheRainbow(self, loops):
        RAINBOW = [COLOUR_RED, COLOUR_ORANGE, COLOUR_YELLOW, COLOUR_GREEN, COLOUR_BLUE, COLOUR_INDIGO, COLOUR_VIOLET]
        DIAG = [[0],[1,4],[2,5,8],[3,6,9,12],[7,10,13],[11,14],[15]]
        self.resetColours(self.getKeyColours())

        for index in range (1, len(RAINBOW) * (loops + 1)):
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

            time.sleep(0.05)
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

    def __init__(self, keyboard, keyboardLayout, setKeyColour):
        self.setKeyColour = setKeyColour
        self.keyboard = keyboard
        self.keyboardLayout= keyboardLayout

    # does the animation for the keys
    def introduce(self):
        self.tasteTheRainbow(5)
        self.resetColours(self.getKeyColours())
        time.sleep(0.2)

    # sets the colours of the keys back to the resting state
    def resetColours(self, colours):
        for key in range(BUTTON_COUNT):
            if len(colours) == 3:
                self.setKeyColour(key, colours)
            elif len(colours) == BUTTON_COUNT:
                self.setKeyColour(key, colours[key][0])

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
            self.tasteTheRainbow(keyIndex)
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
