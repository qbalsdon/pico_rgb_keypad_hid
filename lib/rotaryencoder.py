
import time
import board
from digitalio import DigitalInOut, Direction, Pull

ROTARY_NO_MOTION = 0
ROTARY_CCW       = 1
ROTARY_CW        = 2

class RotaryEncoder:
    def timeInMillis(self):
        return int(time.monotonic() * 1000)

    def __init__(self, aPin=board.GP12, bPin=board.GP10, bluePin=board.GP14):
        self.encoderAPin = DigitalInOut(aPin)
        self.encoderAPin.direction = Direction.INPUT
        self.encoderAPin.pull = Pull.UP

        self.encoderBPin = DigitalInOut(bPin)
        self.encoderBPin.direction = Direction.INPUT
        self.encoderBPin.pull = Pull.UP

        self.loopTime = self.timeInMillis()
        self.encoderA_prev = 0

    # https://www.hobbytronics.co.uk/arduino-tutorial6-rotary-encoder
    def read(self):
        event = ROTARY_NO_MOTION
        # get the current elapsed time
        currentTime = self.timeInMillis()
        if currentTime >= (self.loopTime + 5):
            # 5ms since last check of encoder = 200Hz
            encoderA = self.encoderAPin.value
            encoderB = self.encoderBPin.value
            if (not encoderA) and (self.encoderA_prev):
                # encoder A has gone from high to low
                # CW and CCW determined
                if encoderB:
                    # B is low so counter-clockwise
                    event = ROTARY_CW
                else:
                    # encoder B is high so clockwise
                    event = ROTARY_CCW
            self.encoderA_prev = encoderA # Store value of A for next time
            self.loopTime = currentTime
        return event
