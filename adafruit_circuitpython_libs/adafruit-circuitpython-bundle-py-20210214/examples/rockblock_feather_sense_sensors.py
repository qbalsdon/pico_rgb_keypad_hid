# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

import time
import struct
import board
import adafruit_lsm6ds
import adafruit_lis3mdl
import adafruit_apds9960.apds9960
import adafruit_sht31d
import adafruit_bmp280
import adafruit_rockblock

# RockBlock setup
uart = board.UART()
uart.baudrate = 19200
rb = adafruit_rockblock.RockBlock(uart)

# all the sensors
accelo = adafruit_lsm6ds.LSM6DS33(board.I2C())
magno = adafruit_lis3mdl.LIS3MDL(board.I2C())
prox = adafruit_apds9960.apds9960.APDS9960(board.I2C())
sht = adafruit_sht31d.SHT31D(board.I2C())
bmp = adafruit_bmp280.Adafruit_BMP280_I2C(board.I2C())

# build data
# can decode on other end with struct.unpack("<6fB5f", data)
data = struct.pack("3f", *accelo.acceleration)
data += struct.pack("3f", *magno.magnetic)
data += struct.pack("B", prox.proximity())
data += struct.pack("2f", sht.relative_humidity, sht.temperature)
data += struct.pack("3f", bmp.pressure, bmp.altitude, bmp.temperature)

# send data
rb.data_out = data
print("Talking to satellite...")
retry = 0
status = rb.satellite_transfer()
while status[0] > 8:
    time.sleep(10)
    status = rb.satellite_transfer()
    print(retry, status)
    retry += 1
print("\nDONE.")
