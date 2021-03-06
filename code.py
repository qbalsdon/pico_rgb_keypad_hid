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
USE_DISPLAY = True
if USE_DISPLAY:
    from picodisplay import *
    picoDisplay = PicoDisplay()
    picoDisplay.setBacklightPercent(10)
    wallpapers = [ picoDisplay.getAndroid, picoDisplay.getTeams, picoDisplay.getDota ]
#------------------------------------
from constants import *
from keypad import *
from keyconfig.adb import *
from keyconfig.teams import *
from keyconfig.dota import *
#------------------------------------
for _ in range(10):
    print(" ")
print("  ============ NEW EXECUTION ============  ")
#------------------------------------
interfaces = [ AdbKeypad, TeamsKeypad, DotAKeypad ]
currentInterface = -1
#------------------------------------

# CS  : GP17 - 22
# SCLK: GP18 - 24
# MOSI: GP19 - 25
# ----- I2C -----
# INT : GP3  - 05 ? Not used!
# SDA : GP4  - 06
# SCL : GP5  - 07
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
keypadButtonStates = [ timeDown, timeUp, waiting ]
#------------------------------------
def setKeyColour(pixel, colour):
    pixels[pixel] = (((colour >> 16) & 255), (colour >> 8) & 255, colour & 255)

def swapLayout():
    global currentKeypadConfiguration
    global currentInterface
    currentInterface = (currentInterface + 1) % len(interfaces)
    currentKeypadConfiguration = interfaces[currentInterface](kbd, layout, setKeyColour)
    currentKeypadConfiguration.introduce()
    if USE_DISPLAY:
        picoDisplay.render(wallpapers[currentInterface](), 270)

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
def checkHeldForFlash(heldDownStartMillis):
    if heldDownStartMillis > 0:
        downTime = timeInMillis() - heldDownStartMillis
        picoLED.value = (downTime >= LONG_HOLD and downTime <= LONG_HOLD + 100) or (downTime >= EXTRA_LONG_HOLD and downTime <= EXTRA_LONG_HOLD + 100)
    else:
        picoLED.value = 0
#------------------------------------
if USE_DISPLAY:
    rainbow = picoDisplay.createRainbow()
    rainbow.append(picoDisplay.createText("Welcome", COLOUR_BLACK, 30, 40))
    picoDisplay.render(rainbow, 270)
#------------------------------------
currentKeypadConfiguration = KeypadInterface(kbd, layout, setKeyColour)
currentKeypadConfiguration.introduce()
#------------------------------------
helpMode=False
while True:
    currentKeypadConfiguration.loop()
    if USE_DISPLAY:
        for displayKeyIndex in range(DISPLAY_BUTTON_COUNT):
            buttonValue = checkButton(displayKeyIndex,
                                not picoDisplay.Buttons[displayKeyIndex].value,
                                picoDisplay.ButtonStates,
                                checkHeldForFlash)
            if displayKeyIndex == 0 and buttonValue & EVENT_SINGLE_PRESS:
                swapLayout()
            if displayKeyIndex == 1 and buttonValue & EVENT_SINGLE_PRESS:
                helpMode = True
                # displayHelpMode()

    pressed = read_button_states(0, BUTTON_COUNT)

    for keyIndex in range(BUTTON_COUNT):
        event = checkButton(keyIndex, pressed[keyIndex], keypadButtonStates, checkHeldForFlash)
        if helpMode:
            print(currentKeypadConfiguration.helpForKey(keyIndex))
            helpMode = False
        else:
            currentKeypadConfiguration.handleEvent(keyIndex, event)
