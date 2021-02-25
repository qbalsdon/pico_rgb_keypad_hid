# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

# adafruit_requests usage with a CPython socket
import socket
import ssl
import adafruit_requests

http = adafruit_requests.Session(socket, ssl.create_default_context())

print("Getting CircuitPython star count")
headers = {"Transfer-Encoding": "chunked"}
response = http.get(
    "https://api.github.com/repos/adafruit/circuitpython", headers=headers
)
print("circuitpython stars", response.json()["stargazers_count"])
