#https://github.com/adafruit/Adafruit_CircuitPython_HID/blob/master/adafruit_hid/keycode.py
#------------------------------------
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
from constants import *
from common import *
from adb import *

#------------------------------------
cs = DigitalInOut(board.GP17)
cs.direction = Direction.OUTPUT
cs.value = 0
num_pixels = 16
pixels = adafruit_dotstar.DotStar(board.GP18, board.GP19, num_pixels, brightness=0.2, auto_write=True)
i2c = busio.I2C(board.GP5, board.GP4)
device = I2CDevice(i2c, 0x20)
kbd = Keyboard(usb_hid.devices)
layout = KeyboardLayoutUS(kbd)
held = [0] * num_pixels
lastPress = [0] * num_pixels
#------------------------------------
def setKeyColour(pixel, colour):
    pixels[pixel] = colour

def resetState(colours):
    for i in range(num_pixels):
        if colours != 0:
            setKeyColour(i, colours[i][0])
        #if held[i] == 1:
        #    print("  ~~> [", i ,"] keyUp")
        held[i] = 0

def swapLayout():
    global ki
    ki = AdbKeypadInterface(kbd, layout, setKeyColour, resetState)
    ki.introduce()

def handleKeyDown(keypad, key):
    if key == 15:
        swapLayout()
    else:
        keypad.keyAction(key)

def read_button_states(x, y):
    pressed = [0] * num_pixels
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

def keyPressed(keyIndex):
    setKeyColour(keyIndex, ki.getKeyColours()[keyIndex][1])
    if not held[keyIndex]:
        held[keyIndex] = 1
        handleKeyDown(ki, keyIndex)
#------------------------------------
ki = KeypadInterface(kbd, layout, setKeyColour, resetState)
ki.introduce()

while True:
    pressed = read_button_states(0, num_pixels)

    nonePressed = True
    for keyIndex in range(num_pixels):
        if pressed[keyIndex]:
            keyPressed(keyIndex)
            nonePressed = False

    if nonePressed:
        comboHeld = 0
        resetState(ki.getKeyColours())
    time.sleep(0.1) # Debounce
