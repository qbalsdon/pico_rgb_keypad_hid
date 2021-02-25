# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

import board
import busio
import adafruit_sht31d

# Create library object using our Bus I2C port
i2c = busio.I2C(board.SCL, board.SDA)
sensor = adafruit_sht31d.SHT31D(i2c)

print("\033[1mSensor\033[0m = SHT31-D")
print("\033[1mSerial Number\033[0m = ", sensor.serial_number, "\n")

for i in range(3):
    if i == 0:
        sensor.repeatability = adafruit_sht31d.REP_LOW
        print("\033[1m\033[36mLow Repeatability:\033[0m\n")
    if i == 1:
        sensor.repeatability = adafruit_sht31d.REP_MED
        print("\n\033[1m\033[36mMedium Repeatability:\033[0m\n")
    if i == 2:
        sensor.repeatability = adafruit_sht31d.REP_HIGH
        sensor.clock_stretching = True
        print("\n\033[1m\033[36mHigh Repeatability:\033[0m")
        print("\033[1m\033[95mClock Stretching:\033[0m \033[92mEnabled\033[0m\n")
    for itr in range(3):
        print("\033[1mTemperature:\033[0m %0.3f ºC" % sensor.temperature)
        print("\033[1mHumidity:\033[0m %0.2f %%" % sensor.relative_humidity, "\n")
