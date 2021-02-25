# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

#!/usr/bin/python3
import time
import board
import busio
import adafruit_sht31d

# Create library object using our Bus I2C port
i2c = busio.I2C(board.SCL, board.SDA)
sensor = adafruit_sht31d.SHT31D(i2c)

print("\033[1mSensor\033[0m = SHT31-D")
print("\033[1mSerial Number\033[0m = ", sensor.serial_number, "\n")
sensor.frequency = adafruit_sht31d.FREQUENCY_1
sensor.mode = adafruit_sht31d.MODE_PERIODIC
for i in range(3):
    print("Please wait...", end="\r")
    if i == 2:
        sensor.heater = True
    if i == 1:
        time.sleep(4)
        print("\033[91mCache half full.\033[0m")
    else:
        time.sleep(8)
    if sensor.heater:
        print("\033[1mHeater:\033[0m On    ")
        sensor.heater = False
    print("\033[1mTemperature:\033[0m ", sensor.temperature)
    if not sensor.heater:
        print("\033[1mHeater:\033[0m Off")
    print("\033[1mHumidity:\033[0m ", sensor.relative_humidity, "\n")
sensor.mode = adafruit_sht31d.MODE_SINGLE
