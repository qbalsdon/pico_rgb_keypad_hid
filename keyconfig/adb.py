import time
from constants import *
from adafruit_hid.keycode import Keycode

class AdbKeypadInterface():
    #--- OPTIONAL METHODS ---
    showTerminalDialog="osascript -e 'display dialog \"Can you see a dialog with 2 buttons?\" buttons {\"Ok\", \"Cancel\"} default button \"Ok\"'"
    loadDevice="pkill scrcpy; sleep 0.1 && sh unlockWithSwipe -p 314159 && scrcpy -Sw &"
    listElementIdDialog="sh okDialog -c \"sh listElements -a id\""
    toggleTalkBack="sh talkback"

    def goTerminal(self):
        self.keyboard.send(Keycode.COMMAND, Keycode.SPACE)
        time.sleep(KEYBOARD_DELAY)
        self.keyboardLayout.write("terminal")
        time.sleep(KEYBOARD_DELAY)
        self.keyboard.send(Keycode.RETURN)
        time.sleep(KEYBOARD_DELAY)

    def androidAdbIntro(self):
        self.resetColours(COLOUR_OFF)

        time.sleep(0.2)
        for col in range(4):
            for row in range(4):
                index = (row * 4) + col
                self.setKeyColour(index, self.IMAGE[index])
            time.sleep(ANIMATION_FRAME)

        time.sleep(ANIMATION_WAIT)

    #------------------------
    #----- PICO DISPLAY -----
    def getDisplaySettings(self):
        return ("android", "images/android.bmp")
    #------------------------
    #--- REQUIRED METHODS ---
    IMAGE = [
        COLOUR_WHITE, COLOUR_GREEN, COLOUR_WHITE, COLOUR_WHITE,
        COLOUR_WHITE, COLOUR_WHITE, COLOUR_GREEN, COLOUR_GREEN,
        COLOUR_WHITE, COLOUR_GREEN, COLOUR_GREEN, COLOUR_GREEN,
        COLOUR_GREEN, COLOUR_GREEN, COLOUR_GREEN, COLOUR_GREEN
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
        self.androidAdbIntro()
        self.resetColours(self.getKeyColours())
        time.sleep(0.1)

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
            self.goTerminal()
            self.keyboardLayout.write(self.loadDevice)
            time.sleep(KEYBOARD_DELAY)
            self.keyboard.send(Keycode.RETURN)
        elif index == 1:
            self.goTerminal()
            self.keyboardLayout.write(self.listElementIdDialog)
            time.sleep(KEYBOARD_DELAY)
            self.keyboard.send(Keycode.RETURN)
        elif index == 2:
            self.goTerminal()
            self.keyboardLayout.write(self.toggleTalkBack)
            time.sleep(KEYBOARD_DELAY)
            self.keyboard.send(Keycode.RETURN)
        time.sleep(KEYBOARD_DELAY)
        time.sleep(KEYBOARD_DELAY)
        self.keyboard.send(Keycode.COMMAND, Keycode.TAB)
        time.sleep(KEYBOARD_DELAY)
    #------------------------
