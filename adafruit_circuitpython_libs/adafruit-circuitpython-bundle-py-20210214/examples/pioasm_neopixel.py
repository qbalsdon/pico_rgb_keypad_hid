# SPDX-FileCopyrightText: 2021 Scott Shawcroft, written for Adafruit Industries
#
# SPDX-License-Identifier: MIT

import time
import rp2pio
import board
import adafruit_pioasm

# NeoPixels are 800khz bit streams. Zeroes are 1/3 duty cycle (~416ns) and ones
# are 2/3 duty cycle (~833ns).
program = """
.program ws2812
.side_set 1
.wrap_target
bitloop:
  out x 1        side 0 [1]; Side-set still takes place when instruction stalls
  jmp !x do_zero side 1 [1]; Branch on the bit we shifted out. Positive pulse
do_one:
  jmp  bitloop   side 1 [1]; Continue driving high, for a long pulse
do_zero:
  nop            side 0 [1]; Or drive low, for a short pulse
.wrap
"""

assembled = adafruit_pioasm.assemble(program)

sm = rp2pio.StateMachine(
    assembled,
    frequency=800000 * 6,  # 800khz * 6 clocks per bit
    init=adafruit_pioasm.assemble("set pindirs 1"),
    first_set_pin=board.D12,
    first_sideset_pin=board.D12,
    auto_pull=True,
    out_shift_right=False,
    pull_threshold=8,
)
print("real frequency", sm.frequency)

for i in range(100):
    sm.write(b"\x0a\x00\x00")
    time.sleep(0.1)
print("writes done")

time.sleep(2)
