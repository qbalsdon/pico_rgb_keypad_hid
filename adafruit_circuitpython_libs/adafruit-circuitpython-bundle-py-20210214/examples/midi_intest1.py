# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

import time
import usb_midi
import adafruit_midi

# A subset of messages/events
# pylint: disable=unused-import
from adafruit_midi.timing_clock import TimingClock

# from adafruit_midi.channel_pressure        import ChannelPressure
from adafruit_midi.control_change import ControlChange
from adafruit_midi.note_off import NoteOff
from adafruit_midi.note_on import NoteOn
from adafruit_midi.pitch_bend import PitchBend


# 0 is MIDI channel 1
midi = adafruit_midi.MIDI(midi_in=usb_midi.ports[0], in_channel=0)

print("Midi input test with pauses")

# Convert channel numbers at the presentation layer to the ones musicians use
print("Input channel:", midi.in_channel + 1)

# play with the pause to simulate code doing other stuff
# in the loop
pauses = [0] * 10 + [0.010] * 10 + [0.100] * 10 + [1.0] * 10

while True:
    for pause in pauses:
        msg = midi.receive()
        if msg is not None:
            print(time.monotonic(), msg)
        if pause:
            time.sleep(pause)
