#defines the teams actions
import mappings.common

myButtonState = (
    (COLOUR_GREEN, COLOUR_YELLOW, goTerminal),
    (COLOUR_OFF, COLOUR_CLEAR, noOp),
    (COLOUR_OFF, COLOUR_CLEAR, noOp),
    (COLOUR_OFF, COLOUR_CLEAR, noOp),
    (COLOUR_OFF, COLOUR_CLEAR, noOp),
    (COLOUR_OFF, COLOUR_CLEAR, noOp),
    (COLOUR_OFF, COLOUR_CLEAR, noOp),
    (COLOUR_OFF, COLOUR_CLEAR, noOp),
    (COLOUR_OFF, COLOUR_CLEAR, noOp),
    (COLOUR_OFF, COLOUR_CLEAR, noOp),
    (COLOUR_OFF, COLOUR_CLEAR, noOp),
    (COLOUR_OFF, COLOUR_CLEAR, noOp),
    (COLOUR_OFF, COLOUR_CLEAR, noOp),
    (COLOUR_OFF, COLOUR_CLEAR, noOp),
    (COLOUR_OFF, COLOUR_CLEAR, noOp),
    (COLOUR_OFF, COLOUR_CLEAR, noOp)
)

def teamsMicToggle():
    kbd.send(Keycode.COMMAND, Keycode.SHIFT, Keycode.M)
def teamsCameraToggle():
    kbd.send(Keycode.COMMAND, Keycode.SHIFT, Keycode.O)
def teamsHangUp():
    kbd.send(Keycode.COMMAND, Keycode.SHIFT, Keycode.B)
