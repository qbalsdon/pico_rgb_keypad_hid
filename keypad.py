import time
from constants import *

class KeypadInterface():
    def getKeyColours(self):
        return (
            (COLOUR_OFF, COLOUR_CLEAR),
            (COLOUR_OFF, COLOUR_CLEAR),
            (COLOUR_OFF, COLOUR_CLEAR),
            (COLOUR_OFF, COLOUR_CLEAR),
            (COLOUR_OFF, COLOUR_CLEAR),
            (COLOUR_OFF, COLOUR_CLEAR),
            (COLOUR_OFF, COLOUR_CLEAR),
            (COLOUR_OFF, COLOUR_CLEAR),
            (COLOUR_OFF, COLOUR_CLEAR),
            (COLOUR_OFF, COLOUR_CLEAR),
            (COLOUR_OFF, COLOUR_CLEAR),
            (COLOUR_OFF, COLOUR_CLEAR),
            (COLOUR_OFF, COLOUR_CLEAR),
            (COLOUR_OFF, COLOUR_CLEAR),
            (COLOUR_OFF, COLOUR_CLEAR),
            (COLOUR_YELLOW, COLOUR_WHITE)
        )

    def __init__(self, keyboard, keyboardLayout, setKeyColour, resetState):
        self.setKeyColour = setKeyColour
        self.resetState = resetState
        self.keyboard = keyboard
        self.keyboardLayout= keyboardLayout

    def tasteTheRainbow(self, loops):
        RAINBOW = [COLOUR_RED, COLOUR_ORANGE, COLOUR_YELLOW, COLOUR_GREEN, COLOUR_BLUE, COLOUR_INDIGO, COLOUR_VIOLET]
        DIAG = [[0],[1,4],[2,5,8],[3,6,9,12],[7,10,13],[11,14],[15]]
        self.resetState(self.getKeyColours())

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

    def introduce(self):
        self.tasteTheRainbow(5)
        self.resetState(self.getKeyColours())
        time.sleep(0.2)

    def keyAction(self, index):
        print("      ~~> [",index,"] pressed")
        #self.tasteTheRainbow(index)
