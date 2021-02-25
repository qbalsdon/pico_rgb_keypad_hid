""" Read data from the magnetometer and print it out, ASAP! """

import board
import busio
import adafruit_lsm303

i2c = busio.I2C(board.SCL, board.SDA)
sensor = adafruit_lsm303.LSM303(i2c)

while True:
    mag_x, mag_y, mag_z = sensor.magnetic
    print('{0:10.3f} {1:10.3f} {2:10.3f}'.format(mag_x, mag_y, mag_z))
