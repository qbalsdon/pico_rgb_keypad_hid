# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

# adafruit_requests usage with a CPython socket
import socket
import ssl
import adafruit_requests as requests

https = requests.Session(socket, ssl.create_default_context())

TEXT_URL = "https://httpbin.org/get"
JSON_GET_URL = "https://httpbin.org/get"
JSON_POST_URL = "https://httpbin.org/post"

# print("Fetching text from %s" % TEXT_URL)
# response = requests.get(TEXT_URL)
# print("-" * 40)

# print("Text Response: ", response.text)
# print("-" * 40)
# response.close()

print("Fetching JSON data from %s" % JSON_GET_URL)
response = https.get(JSON_GET_URL)
print("-" * 40)

print("JSON Response: ", response.json())
print("-" * 40)

data = "31F"
print("POSTing data to {0}: {1}".format(JSON_POST_URL, data))
response = https.post(JSON_POST_URL, data=data)
print("-" * 40)

json_resp = response.json()
# Parse out the 'data' key from json_resp dict.
print("Data received from server:", json_resp["data"])
print("-" * 40)

json_data = {"Date": "July 25, 2019"}
print("POSTing data to {0}: {1}".format(JSON_POST_URL, json_data))
response = https.post(JSON_POST_URL, json=json_data)
print("-" * 40)

json_resp = response.json()
# Parse out the 'json' key from json_resp dict.
print("JSON Data received from server:", json_resp["json"])
print("-" * 40)
