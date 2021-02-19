import time
from constants import *
from adafruit_hid.keycode import Keycode

class AdbKeypadInterface():
    #                   osascript -e 'display dialog "Can you see a dialog with 2 buttons?" buttons {"Ok", "Cancel"} default button "Ok"'
    showTerminalDialog="osascript -e 'display dialog \"Can you see a dialog with 2 buttons?\" buttons {\"Ok\", \"Cancel\"} default button \"Ok\"'"
    loadDevice="sh unlockWithSwipe -p 314159 && scrcpy -Sw & SCRCPY_ID=$!"
    killDevice="kill $SCRCPY_ID"
    listElementIdDialog="sh okDialog -c \"sh listElements -a id\""
    toggleTalkBack="sh talkback"

    #def createDialogWithCommand(self, command):
        #return "PARAMETER=\"${$(" + command + ")//$'\\n'/\\\\n}\" && PARAMETER=\"display dialog \\\"$PARAMETER\\\" buttons {\\\"Ok\\\", \\\"Cancel\\\"} default button \\\"Ok\\\"\" && osascript -e $PARAMETER &"

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

    def __init__(self, keyboard, keyboardLayout, setKeyColour, resetState):
        self.setKeyColour = setKeyColour
        self.resetState = resetState
        self.keyboard = keyboard
        self.keyboardLayout= keyboardLayout

    def goBlank(self):
        for index in range(16):
            self.setKeyColour(index, COLOUR_OFF)

    def androidAdbIntro(self):
        self.resetState(COLOUR_OFF)

        time.sleep(0.2)
        for col in range(4):
            for row in range(4):
                index = (row * 4) + col
                self.setKeyColour(index, self.IMAGE[index])
            time.sleep(ANIMATION_FRAME)

        time.sleep(ANIMATION_WAIT)

    def introduce(self):
        self.androidAdbIntro()
        self.resetState(self.getKeyColours())
        time.sleep(0.1)

    def goTerminal(self):
        self.keyboard.send(Keycode.COMMAND, Keycode.SPACE)
        time.sleep(KEYBOARD_DELAY)
        self.keyboardLayout.write("terminal")
        time.sleep(KEYBOARD_DELAY)
        self.keyboard.send(Keycode.RETURN)
        time.sleep(KEYBOARD_DELAY)

    def keyAction(self, index):
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
        elif index == 14:
            self.goTerminal()
            self.keyboardLayout.write(self.killDevice)
            time.sleep(KEYBOARD_DELAY)
            self.keyboard.send(Keycode.RETURN)
