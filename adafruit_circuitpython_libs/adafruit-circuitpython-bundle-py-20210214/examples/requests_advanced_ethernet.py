# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

import board
import busio
from digitalio import DigitalInOut
from adafruit_wiznet5k.adafruit_wiznet5k import WIZNET5K
import adafruit_wiznet5k.adafruit_wiznet5k_socket as socket
import adafruit_requests as requests

cs = DigitalInOut(board.D10)
spi_bus = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)

# Initialize ethernet interface with DHCP
eth = WIZNET5K(spi_bus, cs)

# Initialize a requests object with a socket and ethernet interface
requests.set_socket(socket, eth)

JSON_GET_URL = "http://httpbin.org/get"

attempts = 3  # Number of attempts to retry each request
failure_count = 0
response = None

# Define a custom header as a dict.
headers = {"user-agent": "blinka/1.0.0"}

print("Fetching JSON data from %s..." % JSON_GET_URL)
while not response:
    try:
        response = requests.get(JSON_GET_URL, headers=headers)
        failure_count = 0
    except AssertionError as error:
        print("Request failed, retrying...\n", error)
        failure_count += 1
        if failure_count >= attempts:
            raise AssertionError(
                "Failed to resolve hostname, \
                                  please check your router's DNS configuration."
            ) from error
        continue
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
