# SPDX-FileCopyrightText: 2009 Jordan Terell (blog.jordanterrell.com)
# SPDX-FileCopyrightText: 2020 Brent Rubell for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_wiznet5k_dhcp`
================================================================================

Pure-Python implementation of Jordan Terrell's DHCP library v0.3

* Author(s): Jordan Terrell, Brent Rubell

"""
import gc
import time
from random import randrange
from micropython import const
import adafruit_wiznet5k.adafruit_wiznet5k_socket as socket
from adafruit_wiznet5k.adafruit_wiznet5k_socket import htonl, htons


# DHCP State Machine
STATE_DHCP_START = const(0x00)
STATE_DHCP_DISCOVER = const(0x01)
STATE_DHCP_REQUEST = const(0x02)
STATE_DHCP_LEASED = const(0x03)
STATE_DHCP_REREQUEST = const(0x04)
STATE_DHCP_RELEASE = const(0x05)

# DHCP Message Types
DHCP_DISCOVER = const(1)
DHCP_OFFER = const(2)
DHCP_REQUEST = const(3)
DHCP_DECLINE = const(4)
DHCP_ACK = const(5)
DHCP_NAK = const(6)
DHCP_RELEASE = const(7)
DHCP_INFORM = const(8)

# DHCP Message OP Codes
DHCP_BOOT_REQUEST = const(0x01)
DHCP_BOOT_REPLY = const(0x02)

DHCP_HTYPE10MB = const(0x01)
DHCP_HTYPE100MB = const(0x02)

DHCP_HLENETHERNET = const(0x06)
DHCP_HOPS = const(0x00)

MAGIC_COOKIE = const(0x63825363)
MAX_DHCP_OPT = const(0x10)

# Default DHCP Server port
DHCP_SERVER_PORT = const(67)
# DHCP Lease Time, in seconds
DEFAULT_LEASE_TIME = const(900)
BROADCAST_SERVER_ADDR = "255.255.255.255"

# DHCP Response Options
MSG_TYPE = 53
SUBNET_MASK = 1
ROUTERS_ON_SUBNET = 3
DNS_SERVERS = 6
DHCP_SERVER_ID = 54
T1_VAL = 58
T2_VAL = 59
LEASE_TIME = 51
OPT_END = 255


_BUFF = bytearray(317)


class DHCP:
    """W5k DHCP Client implementation.
    :param eth: Wiznet 5k object
    :param list mac_address: Hardware MAC.
    :param str hostname: The desired hostname, with optional {} to fill in MAC.
    :param int response_timeout: DHCP Response timeout.
    :param bool debug: Enable debugging output.

    """

    # pylint: disable=too-many-arguments, too-many-instance-attributes, invalid-name
    def __init__(
        self, eth, mac_address, hostname=None, response_timeout=30, debug=False
    ):
        self._debug = debug
        self._response_timeout = response_timeout
        self._mac_address = mac_address

        # Initalize a new UDP socket for DHCP
        socket.set_interface(eth)
        self._sock = socket.socket(type=socket.SOCK_DGRAM)
        self._sock.settimeout(response_timeout)

        # DHCP state machine
        self._dhcp_state = STATE_DHCP_START
        self._initial_xid = 0
        self._transaction_id = 0

        # DHCP server configuration
        self.dhcp_server_ip = 0
        self.local_ip = 0
        self.gateway_ip = 0
        self.subnet_mask = 0
        self.dns_server_ip = 0

        # Lease configuration
        self._lease_time = 0
        self._last_check_lease_ms = 0
        self._renew_in_sec = 0
        self._rebind_in_sec = 0
        self._t1 = 0
        self._t2 = 0

        # Host name
        mac_string = "".join("{:02X}".format(o) for o in mac_address)
        self._hostname = bytes(
            (hostname or "WIZnet{}").split(".")[0].format(mac_string)[:42], "utf-8"
        )

    def send_dhcp_message(self, state, time_elapsed):
        """Assemble and send a DHCP message packet to a socket.
        :param int state: DHCP Message state.
        :param float time_elapsed: Number of seconds elapsed since renewal.

        """
        # OP
        _BUFF[0] = DHCP_BOOT_REQUEST
        # HTYPE
        _BUFF[1] = DHCP_HTYPE10MB
        # HLEN
        _BUFF[2] = DHCP_HLENETHERNET
        # HOPS
        _BUFF[3] = DHCP_HOPS

        # Transaction ID (xid)
        self._initial_xid = htonl(self._transaction_id)
        self._initial_xid = self._initial_xid.to_bytes(4, "l")
        _BUFF[4:7] = self._initial_xid

        # seconds elapsed
        _BUFF[8] = (int(time_elapsed) & 0xFF00) >> 8
        _BUFF[9] = int(time_elapsed) & 0x00FF

        # flags
        flags = htons(0x8000)
        flags = flags.to_bytes(2, "b")
        _BUFF[10] = flags[1]
        _BUFF[11] = flags[0]

        # NOTE: Skipping cidaddr/yiaddr/siaddr/giaddr
        # as they're already set to 0.0.0.0

        # chaddr
        _BUFF[28:34] = self._mac_address

        # NOTE:  192 octets of 0's, BOOTP legacy

        # Magic Cookie
        _BUFF[236] = (MAGIC_COOKIE >> 24) & 0xFF
        _BUFF[237] = (MAGIC_COOKIE >> 16) & 0xFF
        _BUFF[238] = (MAGIC_COOKIE >> 8) & 0xFF
        _BUFF[239] = MAGIC_COOKIE & 0xFF

        # Option - DHCP Message Type
        _BUFF[240] = 53
        _BUFF[241] = 0x01
        _BUFF[242] = state

        # Option - Client Identifier
        _BUFF[243] = 61
        # Length
        _BUFF[244] = 0x07
        # HW Type - ETH
        _BUFF[245] = 0x01
        # Client MAC Address
        for mac in range(0, len(self._mac_address)):
            _BUFF[246 + mac] = self._mac_address[mac]

        # Option - Host Name
        _BUFF[252] = 12
        hostname_len = len(self._hostname)
        after_hostname = 254 + hostname_len
        _BUFF[253] = hostname_len
        _BUFF[254:after_hostname] = self._hostname

        if state == DHCP_REQUEST:
            # Set the parsed local IP addr
            _BUFF[after_hostname] = 50
            _BUFF[after_hostname + 1] = 0x04

            _BUFF[after_hostname + 2 : after_hostname + 6] = self.local_ip
            # Set the parsed dhcp server ip addr
            _BUFF[after_hostname + 6] = 54
            _BUFF[after_hostname + 7] = 0x04
            _BUFF[after_hostname + 8 : after_hostname + 12] = self.dhcp_server_ip

        _BUFF[after_hostname + 12] = 55
        _BUFF[after_hostname + 13] = 0x06
        # subnet mask
        _BUFF[after_hostname + 14] = 1
        # routers on subnet
        _BUFF[after_hostname + 15] = 3
        # DNS
        _BUFF[after_hostname + 16] = 6
        # domain name
        _BUFF[after_hostname + 17] = 15
        # renewal (T1) value
        _BUFF[after_hostname + 18] = 58
        # rebinding (T2) value
        _BUFF[after_hostname + 19] = 59
        _BUFF[after_hostname + 20] = 255

        # Send DHCP packet
        self._sock.send(_BUFF)

    def parse_dhcp_response(
        self, response_timeout
    ):  # pylint: disable=too-many-branches, too-many-statements
        """Parse DHCP response from DHCP server.
        Returns DHCP packet type.

        :param int response_timeout: Time to wait for server to return packet, in seconds.
        """
        start_time = time.monotonic()
        packet_sz = self._sock.available()
        while packet_sz <= 0:
            packet_sz = self._sock.available()
            if (time.monotonic() - start_time) > response_timeout:
                return (255, 0)
            time.sleep(0.05)
        # store packet in buffer
        _BUFF = self._sock.recv()
        if self._debug:
            print("DHCP Response: ", _BUFF)

        # -- Parse Packet, FIXED -- #
        # Validate OP
        assert (
            _BUFF[0] == DHCP_BOOT_REPLY
        ), "Malformed Packet - \
            DHCP message OP is not expected BOOT Reply."

        xid = _BUFF[4:8]
        if bytes(xid) < self._initial_xid:
            print("f")
            return 0, 0

        self.local_ip = _BUFF[16:20]
        if _BUFF[28:34] == 0:
            return 0, 0

        if int.from_bytes(_BUFF[235:240], "l") != MAGIC_COOKIE:
            return 0, 0

        # -- Parse Packet, VARIABLE -- #
        ptr = 240
        while _BUFF[ptr] != OPT_END:
            if _BUFF[ptr] == MSG_TYPE:
                ptr += 1
                opt_len = _BUFF[ptr]
                ptr += opt_len
                msg_type = _BUFF[ptr]
                ptr += 1
            elif _BUFF[ptr] == SUBNET_MASK:
                ptr += 1
                opt_len = _BUFF[ptr]
                ptr += 1
                self.subnet_mask = _BUFF[ptr : ptr + opt_len]
                ptr += opt_len
            elif _BUFF[ptr] == DHCP_SERVER_ID:
                ptr += 1
                opt_len = _BUFF[ptr]
                ptr += 1
                self.dhcp_server_ip = _BUFF[ptr : ptr + opt_len]
                ptr += opt_len
            elif _BUFF[ptr] == LEASE_TIME:
                ptr += 1
                opt_len = _BUFF[ptr]
                ptr += 1
                self._lease_time = int.from_bytes(_BUFF[ptr : ptr + opt_len], "l")
                ptr += opt_len
            elif _BUFF[ptr] == ROUTERS_ON_SUBNET:
                ptr += 1
                opt_len = _BUFF[ptr]
                ptr += 1
                self.gateway_ip = _BUFF[ptr : ptr + opt_len]
                ptr += opt_len
            elif _BUFF[ptr] == DNS_SERVERS:
                ptr += 1
                opt_len = _BUFF[ptr]
                ptr += 1
                self.dns_server_ip = _BUFF[ptr : ptr + 4]
                ptr += opt_len  # still increment even though we only read 1 addr.
            elif _BUFF[ptr] == T1_VAL:
                ptr += 1
                opt_len = _BUFF[ptr]
                ptr += 1
                self._t1 = int.from_bytes(_BUFF[ptr : ptr + opt_len], "l")
                ptr += opt_len
            elif _BUFF[ptr] == T2_VAL:
                ptr += 1
                opt_len = _BUFF[ptr]
                ptr += 1
                self._t2 = int.from_bytes(_BUFF[ptr : ptr + opt_len], "l")
                ptr += opt_len
            elif _BUFF[ptr] == 0:
                break
            else:
                # We're not interested in this option
                ptr += 1
                opt_len = _BUFF[ptr]
                ptr += 1
                # no-op
                ptr += opt_len

        if self._debug:
            print(
                "Msg Type: {}\nSubnet Mask: {}\nDHCP Server ID:{}\nDNS Server IP:{}\
                  \nGateway IP:{}\nT1:{}\nT2:{}\nLease Time:{}".format(
                    msg_type,
                    self.subnet_mask,
                    self.dhcp_server_ip,
                    self.dns_server_ip,
                    self.gateway_ip,
                    self._t1,
                    self._t2,
                    self._lease_time,
                )
            )

        gc.collect()
        return msg_type, xid

    def request_dhcp_lease(
        self,
    ):  # pylint: disable=too-many-branches, too-many-statements
        """Request to renew or acquire a DHCP lease."""
        # select an initial transaction id
        self._transaction_id = randrange(1, 2000)

        result = 0
        msg_type = 0
        start_time = time.monotonic()

        while self._dhcp_state != STATE_DHCP_LEASED:
            if self._dhcp_state == STATE_DHCP_START:
                self._transaction_id += 1
                self._sock.connect(((BROADCAST_SERVER_ADDR), DHCP_SERVER_PORT))
                if self._debug:
                    print("* DHCP: Discover")
                self.send_dhcp_message(
                    STATE_DHCP_DISCOVER, ((time.monotonic() - start_time) / 1000)
                )
                self._dhcp_state = STATE_DHCP_DISCOVER
            elif self._dhcp_state == STATE_DHCP_DISCOVER:
                if self._debug:
                    print("* DHCP: Parsing OFFER")
                msg_type, xid = self.parse_dhcp_response(self._response_timeout)
                if msg_type == DHCP_OFFER:
                    # use the _transaction_id the offer returned,
                    # rather than the current one
                    self._transaction_id = self._transaction_id.from_bytes(xid, "l")
                    if self._debug:
                        print("* DHCP: Request")
                    self.send_dhcp_message(
                        DHCP_REQUEST, ((time.monotonic() - start_time) / 1000)
                    )
                    self._dhcp_state = STATE_DHCP_REQUEST
                else:
                    print("* Received DHCP Message is not OFFER")
            elif STATE_DHCP_REQUEST:
                if self._debug:
                    print("* DHCP: Parsing ACK")
                msg_type, xid = self.parse_dhcp_response(self._response_timeout)
                if msg_type == DHCP_ACK:
                    self._dhcp_state = STATE_DHCP_LEASED
                    result = 1
                    if self._lease_time == 0:
                        self._lease_time = DEFAULT_LEASE_TIME
                    if self._t1 == 0:
                        # T1 is 50% of _lease_time
                        self._t1 = self._lease_time >> 1
                    if self._t2 == 0:
                        # T2 is 87.5% of _lease_time
                        self._t2 = self._lease_time - (self._lease_time >> 3)
                    self._renew_in_sec = self._t1
                    self._rebind_in_sec = self._t2
                elif msg_type == DHCP_NAK:
                    self._dhcp_state = STATE_DHCP_START
                else:
                    print("* Received DHCP Message is not OFFER")

                if msg_type == 255:
                    msg_type = 0
                    self._dhcp_state = STATE_DHCP_START

            if result != 1 and (
                (time.monotonic() - start_time > self._response_timeout)
            ):
                break

        self._transaction_id += 1
        self._last_check_lease_ms = time.monotonic()
        # close the socket, we're done with it
        self._sock.close()
        gc.collect()
        return result
