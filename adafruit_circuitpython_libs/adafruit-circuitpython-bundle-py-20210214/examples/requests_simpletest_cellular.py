# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

# pylint: disable=unused-import
import time
import board
import busio
import digitalio
from adafruit_fona.adafruit_fona import FONA
from adafruit_fona.fona_3g import FONA3G
import adafruit_fona.adafruit_fona_network as network
import adafruit_fona.adafruit_fona_socket as cellular_socket
import adafruit_requests as requests

# Get GPRS details and more from a secrets.py file
try:
    from secrets import secrets
except ImportError:
    print("GPRS secrets are kept in secrets.py, please add them there!")
    raise

# Create a serial connection for the FONA connection
uart = busio.UART(board.TX, board.RX)
rst = digitalio.DigitalInOut(board.D4)

# Use this for FONA800 and FONA808
fona = FONA(uart, rst)

# Use this for FONA3G
# fona = FONA3G(uart, rst)

# Initialize cellular data network
network = network.CELLULAR(
    fona, (secrets["apn"], secrets["apn_username"], secrets["apn_password"])
)

while not network.is_attached:
    print("Attaching to network...")
    time.sleep(0.5)
print("Attached!")

while not network.is_connected:
    print("Connecting to network...")
    network.connect()
    time.sleep(0.5)
print("Network Connected!")

# Initialize a requests object with a socket and cellular interface
requests.set_socket(cellular_socket, fona)

TEXT_URL = "http://wifitest.adafruit.com/testwifi/index.html"
JSON_GET_URL = "http://httpbin.org/get"
JSON_POST_URL = "http://httpbin.org/post"

print("Fetching text from %s" % TEXT_URL)
response = requests.get(TEXT_URL)
print("-" * 40)

print("Text Response: ", response.text)
print("-" * 40)
response.close()

print("Fetching JSON data from %s" % JSON_GET_URL)
response = requests.get(JSON_GET_URL)
print("-" * 40)

print("JSON Response: ", response.json())
print("-" * 40)
response.close()

data = "31F"
print("POSTing data to {0}: {1}".format(JSON_POST_URL, data))
response = requests.post(JSON_POST_URL, data=data)
print("-" * 40)

json_resp = response.json()
# Parse out the 'data' key from json_resp dict.
print("Data received from server:", json_resp["data"])
print("-" * 40)
response.close()

json_data = {"Date": "July 25, 2019"}
print("POSTing data to {0}: {1}".format(JSON_POST_URL, json_data))
response = requests.post(JSON_POST_URL, json=json_data)
print("-" * 40)

json_resp = response.json()
# Parse out the 'json' key from json_resp dict.
print("JSON Data received from server:", json_resp["json"])
print("-" * 40)
response.close()
