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

TEXT_URL = "http://wifitest.adafruit.com/testwifi/index.html"
JSON_GET_URL = "http://httpbin.org/get"
JSON_POST_URL = "http://httpbin.org/post"

attempts = 3  # Number of attempts to retry each request
failure_count = 0
response = None

print("Fetching text from %s" % TEXT_URL)
while not response:
    try:
        response = requests.get(TEXT_URL)
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
print("-" * 40)

print("Text Response: ", response.text)
print("-" * 40)
response.close()
response = None

print("Fetching JSON data from %s" % JSON_GET_URL)
while not response:
    try:
        response = requests.get(JSON_GET_URL)
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
print("-" * 40)

print("JSON Response: ", response.json())
print("-" * 40)
response.close()
response = None

data = "31F"
print("POSTing data to {0}: {1}".format(JSON_POST_URL, data))
while not response:
    try:
        response = requests.post(JSON_POST_URL, data=data)
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
print("-" * 40)

json_resp = response.json()
# Parse out the 'data' key from json_resp dict.
print("Data received from server:", json_resp["data"])
print("-" * 40)
response.close()
response = None

json_data = {"Date": "July 25, 2019"}
print("POSTing data to {0}: {1}".format(JSON_POST_URL, json_data))
while not response:
    try:
        response = requests.post(JSON_POST_URL, json=json_data)
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
print("-" * 40)

json_resp = response.json()
# Parse out the 'json' key from json_resp dict.
print("JSON Data received from server:", json_resp["json"])
print("-" * 40)
response.close()
