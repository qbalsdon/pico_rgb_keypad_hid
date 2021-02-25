# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-FileCopyrightText: 2021 Adam Cummick
#
# SPDX-License-Identifier: MIT

import board
import busio
import digitalio
from adafruit_wiznet5k.adafruit_wiznet5k import WIZNET5K
import adafruit_wiznet5k.adafruit_wiznet5k_socket as socket

print("Wiznet5k SimpleServer Test")

# For Adafruit Ethernet FeatherWing
cs = digitalio.DigitalInOut(board.D10)
# For Particle Ethernet FeatherWing
# cs = digitalio.DigitalInOut(board.D5)
spi_bus = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)

# Initialize ethernet interface
eth = WIZNET5K(spi_bus, cs, is_dhcp=False)

# Initialize a socket for our server
socket.set_interface(eth)
server = socket.socket()  # Allocate socket for the server
server_ip = "192.168.10.1"  # IP address of server
server_port = 50007  # Port to listen on
server.bind((server_ip, server_port))  # Bind to IP and Port
server.listen()  # Begin listening for incoming clients

while True:
    conn, addr = server.accept()  # Wait for a connection from a client.
    with conn:
        data = conn.recv()
        print(data)
        conn.send(data)  # Echo message back to client
