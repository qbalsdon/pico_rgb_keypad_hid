# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

import board
import busio
import digitalio
import adafruit_requests as requests
from adafruit_wiznet5k.adafruit_wiznet5k import WIZNET5K
import adafruit_wiznet5k.adafruit_wiznet5k_socket as socket

TEXT_URL = "http://wifitest.adafruit.com/testwifi/index.html"

# Setup your network configuration below
IP_ADDRESS = (192, 168, 10, 1)
SUBNET_MASK = (255, 255, 0, 0)
GATEWAY_ADDRESS = (192, 168, 0, 1)
DNS_SERVER = (8, 8, 8, 8)

print("Wiznet5k WebClient Test (no DHCP)")

cs = digitalio.DigitalInOut(board.D10)
spi_bus = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)

# Initialize ethernet interface without DHCP
eth = WIZNET5K(spi_bus, cs, is_dhcp=False)

# Set network configuration
eth.ifconfig = (IP_ADDRESS, SUBNET_MASK, GATEWAY_ADDRESS, DNS_SERVER)

# Initialize a requests object with a socket and ethernet interface
requests.set_socket(socket, eth)

print("Chip Version:", eth.chip)
print("MAC Address:", [hex(i) for i in eth.mac_address])
print("My IP address is:", eth.pretty_ip(eth.ip_address))
print(
    "IP lookup adafruit.com: %s" % eth.pretty_ip(eth.get_host_by_name("adafruit.com"))
)

# eth._debug = True
print("Fetching text from", TEXT_URL)
r = requests.get(TEXT_URL)
print("-" * 40)
print(r.text)
print("-" * 40)
r.close()

print()
