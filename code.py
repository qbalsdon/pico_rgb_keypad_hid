import time
import board
import busio
import usb_hid

from adafruit_bus_device.i2c_device import I2CDevice
import adafruit_dotstar

from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keyboard_layout_us import KeyboardLayoutUS
from adafruit_hid.keycode import Keycode

from adafruit_hid.consumer_control import ConsumerControl
from adafruit_hid.consumer_control_code import ConsumerControlCode

from digitalio import DigitalInOut, Direction, Pull
#------------------------------------
# from picodisplay import *
# picoDisplay = PicoDisplay()
# wallpapers = [picoDisplay.getAndroid, picoDisplay.getTeams, picoDisplay.getDota]
#------------------------------------
from constants import *
from keypad import *
from keyconfig.adb import *
from keyconfig.teams import *
from keyconfig.dota import *
#------------------------------------
interfaces = [AdbKeypadInterface, TeamsKeypadInterface, DotAKeypadInterface]
currentInterface = -1
#------------------------------------
cs = DigitalInOut(board.GP17)
cs.direction = Direction.OUTPUT
cs.value = 0
pixels = adafruit_dotstar.DotStar(board.GP18, board.GP19, BUTTON_COUNT, brightness=0.2, auto_write=True)
i2c = busio.I2C(board.GP5, board.GP4)
device = I2CDevice(i2c, 0x20)
kbd = Keyboard(usb_hid.devices)
layout = KeyboardLayoutUS(kbd)
#------------------------------------
picoLED = DigitalInOut(board.GP25)
picoLED.direction = Direction.OUTPUT
picoLED.value = 0
#------------------------------------
timeDown = [-1] * BUTTON_COUNT
timeUp = [-1] * BUTTON_COUNT
waiting = [False] * BUTTON_COUNT
#------------------------------------
def setKeyColour(pixel, colour):
    pixels[pixel] = (((colour >> 16) & 255), (colour >> 8) & 255, colour & 255)

def swapLayout():
    global ki
    global currentInterface
    currentInterface = (currentInterface + 1) % len(interfaces)
    ki = interfaces[currentInterface](kbd, layout, setKeyColour)
    # picoDisplay.render(wallpapers[currentInterface](), 270)
    ki.introduce()

def read_button_states(x, y):
    pressed = [0] * BUTTON_COUNT
    with device:
        device.write(bytes([0x0]))
        result = bytearray(2)
        device.readinto(result)
        b = result[0] | result[1] << 8
        for i in range(x, y):
            if not (1 << i) & b:
                pressed[i] = 1
            else:
                pressed[i] = 0
    return pressed
#------------------------------------
def checkHeldForFlash(timeDown):
    if timeDown > 0:
        downTime = timeInMillis() - timeDown
        picoLED.value = (downTime >= LONG_HOLD and downTime <= LONG_HOLD + 100) or (downTime >= EXTRA_LONG_HOLD and downTime <= EXTRA_LONG_HOLD + 100)

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
def checkButton(isPressed, index):
    global timeDown
    global timeUp
    currentTime = timeInMillis()
    lengthDown = -1
    event = EVENT_NONE

    checkHeldForFlash(timeDown[index])

    if isPressed == 1 and timeDown[index] < 0:
        timeDown[index] = currentTime
        event += EVENT_KEY_DOWN
    if isPressed == 0 and timeDown[index] > 0:
        picoLED.value = 0
        event += EVENT_KEY_UP
        lengthDown = currentTime - timeDown[index]
        lengthUp = currentTime - timeUp[index]
        timeUp[index] = currentTime
        timeDown[index] = -1
        waiting[index] = True

        if lengthUp < DOUBLE_GAP:
            # double press
            waiting[index] = False
            event += EVENT_DOUBLE_PRESS

    if waiting[index] and lengthDown >= EXTRA_LONG_HOLD:
        #extra long press
        waiting[index] = False
        event += EVENT_EXTRA_LONG_PRESS

    if waiting[index] and lengthDown >= LONG_HOLD:
        #long press
        waiting[index] = False
        event += EVENT_LONG_PRESS

    lengthUp = currentTime - timeUp[index]
    if waiting[index] and lengthUp >= DOUBLE_GAP:
        #single press
        waiting[index] = False
        event += EVENT_SINGLE_PRESS
    return event
#------------------------------------
# rainbow = picoDisplay.createRainbow()
# picoDisplay.render(rainbow, 270)
#------------------------------------
ki = KeypadInterface(kbd, layout, setKeyColour)
ki.introduce()
#------------------------------------
while True:

    pressed = read_button_states(0, BUTTON_COUNT)

    for keyIndex in range(BUTTON_COUNT):
        event = checkButton(pressed[keyIndex], keyIndex)
        ki.handleEvent(keyIndex, event)
        if keyIndex == 15 and event & EVENT_EXTRA_LONG_PRESS:
            swapLayout()
