import time
from constants import *
from adafruit_hid.keycode import Keycode

class AdbKeypadInterface():
    showTerminalDialog="osascript -e 'display dialog \"Can you see a dialog with 2 buttons?\" buttons {\"Ok\", \"Cancel\"} default button \"Ok\"'"
    def getKeyColours(self):
        return (
            (COLOUR_CLEAR, COLOUR_GREEN),
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
            (COLOUR_OFF, COLOUR_CLEAR)
        )

    def __init__(self, keyboard, keyboardLayout, setKeyColour, resetState):
        self.setKeyColour = setKeyColour
        self.resetState = resetState
        self.keyboard = keyboard
        self.keyboardLayout= keyboardLayout

    def androidAdbIntro(self):
        self.resetState(self.getKeyColours())
        image = [ COLOUR_WHITE, COLOUR_GREEN, COLOUR_WHITE, COLOUR_WHITE, COLOUR_WHITE, COLOUR_WHITE, COLOUR_GREEN, COLOUR_GREEN, COLOUR_WHITE, COLOUR_GREEN, COLOUR_GREEN, COLOUR_GREEN, COLOUR_GREEN, COLOUR_GREEN, COLOUR_GREEN, COLOUR_GREEN]
        for col in range(4):
            for row in range(4):
                index = (row * 4) + col
                self.setKeyColour(index, image[index])
            time.sleep(0.05)
        time.sleep(0.5)

    def introduce(self):
        self.androidAdbIntro()
        self.resetState(self.getKeyColours())
        time.sleep(0.2)

    def keyAction(self, index):
        if index == 0:
            self.keyboard.send(Keycode.COMMAND, Keycode.SPACE)
            time.sleep(0.1)
            self.keyboardLayout.write("terminal")
            time.sleep(0.1)
            self.keyboard.send(Keycode.RETURN)
            time.sleep(0.1)
            self.keyboardLayout.write(self.showTerminalDialog)
            time.sleep(0.1)
            self.keyboard.send(Keycode.RETURN)
