from digitalio import DigitalInOut, Direction, Pull

from rgbled import *
from rotaryencoder import *

rotaryEncoder = RotaryEncoder()
rgbLed = RgbLed()

switchPin = DigitalInOut(board.GP15)
switchPin.direction = Direction.INPUT
switchPin.pull = Pull.DOWN

currentValue = 0
while True:
    rotaryValue = rotaryEncoder.read()
    if rotaryValue == ROTARY_CW:
        print("    ~~> rotary increase [clockwise]")
        currentValue = currentValue + 1
    elif rotaryValue == ROTARY_CCW:
        print("    ~~> rotary decrease [counter clockwise]")
        currentValue = currentValue - 1

    if currentValue > 255:
        currentValue = 0
    if currentValue < 0:
        currentValue = 255
    colour = rgbLed.colourWheel(currentValue)
    rgbLed.setColour(colour[0], colour[1], colour[2])


    if switchPin.value:
        rgbLed.setColour(0xffffff)
