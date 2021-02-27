"""
# Things I should have read:
1. https://www.hackster.io/techmirtz/using-common-cathode-and-common-anode-rgb-led-with-arduino-7f3aa9
   This fisrt of all tells you how the different RGB LED's work, and give a helpful diagram:
   ![Common Anode / Cathode](https://hackster.imgix.net/uploads/attachments/333485/rgb-led_8qitceRYYl.png?auto=compress%2Cformat&w=740&h=555&fit=max)
1. The datasheet: http://cdn.sparkfun.com/datasheets/Components/Switches/EC12PLRGBSDVBF-D-25K-24-24C-6108-6HSPEC.pdf
   While it's awful, it's something. And at least it's only 12 pages of awful, and let's be honest, I can't be blamed for not understanding half of it because I'm pretty sure that ain't English
   Looking at the wiring and comparing to the diagram you can see that it's **common anode**
1. PWM: https://cdn-learn.adafruit.com/downloads/pdf/getting-started-with-raspberry-pi-pico-circuitpython.pdf
   On page 82, they do mention using a different pin in the case of a ValueError, however I had to use
"""
import time
import board
from pwmio import PWMOut

PWM_FREQ  = 5000
COLOUR_MAX = 65535

class RgbLed:
    # Converts a value that exists within a range to a value in another range
    def convertScale(self, value, originMin=0, originMax=255, destinationMin=0, destinationMax=COLOUR_MAX):
        originSpan = originMax - originMin
        destinationSpan = destinationMax - destinationMin
        scaledValue = float(value - originMin) / float(originSpan)
        return destinationMin + (scaledValue * destinationSpan)

    # This method ensures the value is in the range [0-255]
    # it then maps the value to a number between [0-65535]
    # it then inverts the value
    def normalise(self, colourElement):
        value = colourElement
        if value > 255:
            value = 255
        if value < 0:
            value = 0
        return COLOUR_MAX - int(self.convertScale(value))

    def setColourRGB(self, red, green, blue):
         self.rPin.duty_cycle = self.normalise(red)
         self.gPin.duty_cycle = self.normalise(green)
         self.bPin.duty_cycle = self.normalise(blue)

    def setColour(self, colour, x = None, y = None):
        if x != None and y != None:
            self.setColourRGB(colour, x, y)
        else:
            self.setColourRGB(
                (colour >> 16) & 255,
                (colour >> 8) & 255,
                colour & 255)

    def colourWheel(self, pos):
        # Input a value 0 to 255 to get a color value.
        # The colours are a transition r - g - b - back to r.
        if pos < 0 or pos > 255:
            return 0, 0, 0
        if pos < 85:
            return int(255 - pos * 3), int(pos * 3), 0
        if pos < 170:
            pos -= 85
            return 0, int(255 - pos * 3), int(pos * 3)
        pos -= 170
        return int(pos * 3), 0, int(255 - (pos * 3))

    def __init__(self, redPin=board.GP11, greenPin=board.GP13, bluePin=board.GP14):
        self.rPin = PWMOut(redPin,   frequency=PWM_FREQ, duty_cycle = COLOUR_MAX)
        self.gPin = PWMOut(greenPin, frequency=PWM_FREQ, duty_cycle = COLOUR_MAX)
        self.bPin = PWMOut(bluePin,  frequency=PWM_FREQ, duty_cycle = COLOUR_MAX)
