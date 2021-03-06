import time

BUTTON_COUNT = 16

DOUBLE_GAP = 250
LONG_HOLD = 1000
EXTRA_LONG_HOLD = 3000

EVENT_NONE             = 0x00
EVENT_SINGLE_PRESS     = 0x01
EVENT_DOUBLE_PRESS     = 0x02
EVENT_LONG_PRESS       = 0x04
EVENT_EXTRA_LONG_PRESS = 0x08
EVENT_KEY_DOWN         = 0x10
EVENT_KEY_UP           = 0x20

KEYBOARD_DELAY = 0.2
ANIMATION_FRAME = 0.15
ANIMATION_WAIT = 0.25
ANIMATION_FRAME_MILLIS = 50

COLOUR_WHITE  = 0xFFFFFF
COLOUR_RED    = 0xFF0000
COLOUR_ORANGE = 0xFFA500
COLOUR_YELLOW = 0xFFFF00
COLOUR_GREEN  = 0x00FF00
COLOUR_BLUE   = 0x0000FF
COLOUR_INDIGO = 0x4B0082
COLOUR_VIOLET = 0x8F00FF
COLOUR_CLEAR  = 0x080808
COLOUR_OFF    = 0x000000
COLOUR_BLACK  = 0x000000

RAINBOW = [ COLOUR_RED, COLOUR_ORANGE, COLOUR_YELLOW, COLOUR_GREEN, COLOUR_BLUE, COLOUR_INDIGO, COLOUR_VIOLET ]

COLOUR_ANDROID_GREEN  = 0x44de97
COLOUR_ANDROID_BLUE   = 0x013f54

COLOUR_TEAMS = 0x505ca1
COLOUR_DOTA = 0xf45045

COLOUR_WHITE_MID   = 0x808080
COLOUR_DARK_RED    = 0x800000
COLOUR_DARK_ORANGE = 0x805200
COLOUR_DARK_YELLOW = 0x808000
COLOUR_DARK_GREEN  = 0x008000
COLOUR_DARK_BLUE   = 0x000080
COLOUR_DARK_INDIGO = 0x250041
COLOUR_DARK_VIOLET = 0x740080

def noOp():
    pass

def timeInMillis():
    return int(time.monotonic() * 1000)

def darkVersion(colour):
    if colour == COLOUR_RED:
        return COLOUR_DARK_RED
    if colour == COLOUR_ORANGE:
        return COLOUR_DARK_ORANGE
    if colour == COLOUR_YELLOW:
        return COLOUR_DARK_YELLOW
    if colour == COLOUR_GREEN:
        return COLOUR_DARK_GREEN
    if colour == COLOUR_BLUE:
        return COLOUR_DARK_BLUE
    if colour == COLOUR_INDIGO:
        return COLOUR_DARK_INDIGO
    if colour == COLOUR_VIOLET:
        return COLOUR_DARK_VIOLET
    if colour == COLOUR_WHITE:
        return COLOUR_WHITE_MID

# takes a button state and checks if the button is
# down or up. It then attempts to determine the past
# states of the button to see if the button belongs
# to one of the following possible events:
#   - EVENT_NONE
#   - EVENT_SINGLE_PRESS,
#   - EVENT_DOUBLE_PRESS,
#   - EVENT_LONG_PRESS,
#   - EVENT_EXTRA_LONG_PRESS
#   - EVENT_KEY_DOWN
#   - EVENT_KEY_UP
def checkButton(index, isButtonDown, buttonStates, longHoldFeedback):
    currentTime = timeInMillis()
    lengthDown = -1
    event = EVENT_NONE
    onButtonDownMillis   = buttonStates[0]
    onButtonLastUpMillis = buttonStates[1]
    isButtonWaiting      = buttonStates[2]

    longHoldFeedback(onButtonDownMillis[index])

    if isButtonDown == 1 and onButtonDownMillis[index] < 0:
        onButtonDownMillis[index] = currentTime
        event += EVENT_KEY_DOWN
    if isButtonDown == 0 and onButtonDownMillis[index] > 0:
        longHoldFeedback(0)
        event += EVENT_KEY_UP
        lengthDown = currentTime - onButtonDownMillis[index]
        lengthUp = currentTime - onButtonLastUpMillis[index]
        onButtonLastUpMillis[index] = currentTime
        onButtonDownMillis[index] = -1
        isButtonWaiting[index] = True

        if lengthUp < DOUBLE_GAP:
            # double press
            isButtonWaiting[index] = False
            event += EVENT_DOUBLE_PRESS

    if isButtonWaiting[index] and lengthDown >= EXTRA_LONG_HOLD:
        #extra long press
        isButtonWaiting[index] = False
        event += EVENT_EXTRA_LONG_PRESS

    if isButtonWaiting[index] and lengthDown >= LONG_HOLD:
        #long press
        isButtonWaiting[index] = False
        event += EVENT_LONG_PRESS

    lengthUp = currentTime - onButtonLastUpMillis[index]
    if isButtonWaiting[index] and lengthUp >= DOUBLE_GAP:
        #single press
        isButtonWaiting[index] = False
        event += EVENT_SINGLE_PRESS
    return event
