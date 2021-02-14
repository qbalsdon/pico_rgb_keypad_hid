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

COLOUR_RED    = [0xFF, 0x00, 0x00]
COLOUR_ORANGE = [0xFF, 0xA5, 0x00]
COLOUR_YELLOW = [0xFF, 0xFF, 0x00]
COLOUR_GREEN  = [0x00, 0xFF, 0x00]
COLOUR_BLUE   = [0x00, 0x00, 0xFF]
COLOUR_INDIGO = [0x4B, 0x00, 0x82]
COLOUR_VIOLET = [0x8F, 0x00, 0xFF]
COLOUR_CLEAR  = [0x08, 0x08, 0x08]


cs = DigitalInOut(board.GP17)
cs.direction = Direction.OUTPUT
cs.value = 0
num_pixels = 16
pixels = adafruit_dotstar.DotStar(board.GP18, board.GP19, num_pixels, brightness=0.1, auto_write=True)
i2c = busio.I2C(board.GP5, board.GP4)
device = I2CDevice(i2c, 0x20)
kbd = Keyboard(usb_hid.devices)
layout = KeyboardLayoutUS(kbd)
held = [0] * num_pixels

def setKeyColour(pixel, colour):
    pixels[pixel] = (colour[0], colour[1], colour[2])

def resetState():
    for i in range(num_pixels):
        setKeyColour(i, COLOUR_CLEAR)
        held[i] = 0

def tasteTheRainbow(loops):
    RAINBOW = [COLOUR_RED, COLOUR_ORANGE, COLOUR_YELLOW, COLOUR_GREEN, COLOUR_BLUE, COLOUR_INDIGO, COLOUR_VIOLET]
    DIAG = [[0],[1,4],[2,5,8],[3,6,9,12],[7,10,13],[11,14],[15]]
    resetState()

    for index in range (1, len(RAINBOW) * (loops + 1)):
        currentColourIndex = 0
        for snakeIndex in range(index - (len(RAINBOW)), index):
            if snakeIndex >=0:
                currentIndex = snakeIndex % len(DIAG)
                currentDiag = DIAG[currentIndex]
                currentColour = RAINBOW[currentColourIndex]
                for button in currentDiag:
                    setKeyColour(button, currentColour)
                currentIndex-=1
                currentColourIndex+=1

        time.sleep(0.05)

tasteTheRainbow(5)
resetState()
time.sleep(0.2)

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
    setKeyColour(keyIndex, COLOUR_GREEN)
    if not held[keyIndex]:
        #layout.write("volu")
        #kbd.send(Keycode.ENTER)
        held[keyIndex] = 1

while True:
    pressed = read_button_states(0, num_pixels)

    nonePressed = True
    for keyIndex in range(num_pixels):
        if pressed[keyIndex]:
            keyPressed(keyIndex)
            nonePressed = False

    if nonePressed:
        resetState()
    time.sleep(0.1) # Debounce
