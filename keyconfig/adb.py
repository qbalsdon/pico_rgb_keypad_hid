import time
from constants import *
from adafruit_hid.keycode import Keycode

class AdbKeypad():
    #--- OPTIONAL METHODS ---
    showTerminalDialog="osascript -e 'display dialog \"Can you see a dialog with 2 buttons?\" buttons {\"Ok\", \"Cancel\"} default button \"Ok\"'"
    loadDevice              = "pkill scrcpy; sleep 0.1 && sh unlockWithSwipe -p 314159 && scrcpy -Sw &"
    loadDeviceButAllowTouch = "pkill scrcpy; sleep 0.1 && sh unlockWithSwipe -p 314159 && scrcpy -w &"
    killConnection          = "pkill scrcpy"
    listElementIdDialog="sh okDialog -c \"sh listElements -a id\""
    toggleTalkBack="sh talkback"
    openTalkBackSettings="sh talkback -o"

    def goTerminal(self):
        self.keyboard.send(Keycode.COMMAND, Keycode.SPACE)
        time.sleep(KEYBOARD_DELAY)
        self.keyboardLayout.write("terminal")
        time.sleep(KEYBOARD_DELAY)
        self.keyboard.send(Keycode.RETURN)
        time.sleep(KEYBOARD_DELAY)

    def androidAdbIntro(self, frame):
        if frame >= 4:
            return
        for row in range(4):
            index = (row * 4) + frame
            self.setKeyColour(index, self.IMAGE[index])
    #------------------------
    #--- REQUIRED METHODS ---
    IMAGE = [
        COLOUR_WHITE, COLOUR_GREEN, COLOUR_WHITE, COLOUR_WHITE,
        COLOUR_WHITE, COLOUR_WHITE, COLOUR_GREEN, COLOUR_GREEN,
        COLOUR_WHITE, COLOUR_GREEN, COLOUR_GREEN, COLOUR_GREEN,
        COLOUR_GREEN, COLOUR_GREEN, COLOUR_GREEN, COLOUR_GREEN
        ]

    def loop(self):
        if self.startAnimationTime > 0:
            estimatedFrame = int((timeInMillis() - self.startAnimationTime) / (ANIMATION_FRAME_MILLIS * 2))
            if estimatedFrame > self.currentFrame:
                # render new animation frame
                self.androidAdbIntro(self.frameIndex)
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
        if event & EVENT_LONG_PRESS:
            if index == 0:
                self.goTerminal()
                self.keyboardLayout.write(self.loadDeviceButAllowTouch)
                time.sleep(KEYBOARD_DELAY)
                self.keyboard.send(Keycode.RETURN)
        if event & EVENT_DOUBLE_PRESS:
            if index == 0:
                self.goTerminal()
                self.keyboardLayout.write(self.killConnection)
                time.sleep(KEYBOARD_DELAY)
                self.keyboard.send(Keycode.RETURN)

        if event & EVENT_SINGLE_PRESS:
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
            elif index == 3:
                self.goTerminal()
                self.keyboardLayout.write(self.openTalkBackSettings)
                time.sleep(KEYBOARD_DELAY)
                self.keyboard.send(Keycode.RETURN)
            time.sleep(KEYBOARD_DELAY)
            time.sleep(KEYBOARD_DELAY)
            self.keyboard.send(Keycode.COMMAND, Keycode.TAB)
            time.sleep(KEYBOARD_DELAY)
    #------------------------
