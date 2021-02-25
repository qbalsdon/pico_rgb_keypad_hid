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
rst = digitalio.DigitalInOut(board.D9)

# Use this for FONA800 and FONA808
# fona = FONA(uart, rst)

# Use this for FONA3G
fona = FONA3G(uart, rst)

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

JSON_GET_URL = "http://httpbin.org/get"

# Define a custom header as a dict.
headers = {"user-agent": "blinka/1.0.0"}

print("Fetching JSON data from %s..." % JSON_GET_URL)
response = requests.get(JSON_GET_URL, headers=headers)
print("-" * 60)

json_data = response.json()
headers = json_data["headers"]
print("Response's Custom User-Agent Header: {0}".format(headers["User-Agent"]))
print("-" * 60)

# Read Response's HTTP status code
print("Response HTTP Status Code: ", response.status_code)
print("-" * 60)

# Read Response, as raw bytes instead of pretty text
print("Raw Response: ", response.content)

# Close, delete and collect the response data
response.close()
