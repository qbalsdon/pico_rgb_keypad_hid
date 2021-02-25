# SPDX-FileCopyrightText: Limor Fried/Ladyada for Adafruit Industries
# SPDX-FileCopyrightText: 2020 Brent Rubell for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_fona`
================================================================================

CircuitPython library for the Adafruit FONA cellular module

* Author(s): ladyada, Brent Rubell

Implementation Notes
--------------------

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://github.com/adafruit/circuitpython/releases

"""
import time
from micropython import const
from simpleio import map_range

__version__ = "2.1.2"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_FONA.git"

FONA_DEFAULT_TIMEOUT_MS = 500  # TODO: Check this against arduino...

# Commands
CMD_AT = b"AT"
# Replies
REPLY_OK = b"OK"
REPLY_AT = b"AT"

# Maximum number of fona800 and fona808 sockets
FONA_MAX_SOCKETS = const(6)

# FONA Versions
FONA_800_L = const(0x01)
FONA_800_H = const(0x6)
FONA_808_V1 = const(0x2)
FONA_808_V2 = const(0x3)
FONA_3G_A = const(0x4)
FONA_3G_E = const(0x5)

# FONA preferred SMS storage
FONA_SMS_STORAGE_SIM = b'"SM"'  # Storage on the SIM
FONA_SMS_STORAGE_INTERNAL = b'"ME"'  # Internal storage on the FONA


# pylint: disable=too-many-instance-attributes, too-many-public-methods
class FONA:
    """CircuitPython FONA module interface.
    :param ~busio.uart UART: FONA UART connection.
    :param ~digialio RST: FONA RST pin.
    :param ~digialio RI: Optional FONA Ring Interrupt (RI) pin.
    :param bool debug: Enable debugging output.

    """

    TCP_MODE = const(0)  # TCP socket
    UDP_MODE = const(1)  # UDP socket

    # pylint: disable=too-many-arguments
    def __init__(self, uart, rst, ri=None, debug=False):
        self._buf = b""  # shared buffer
        self._fona_type = 0
        self._debug = debug

        self._uart = uart
        self._rst = rst
        self._ri = ri
        if self._ri is not None:
            self._ri.switch_to_input()
        if not self._init_fona():
            raise RuntimeError("Unable to find FONA. Please check connections.")

    # pylint: disable=too-many-branches, too-many-statements
    def _init_fona(self):
        """Initializes FONA module."""
        self.reset()

        timeout = 7000
        while timeout > 0:
            if self._send_check_reply(CMD_AT, reply=REPLY_OK):
                break
            if self._send_check_reply(CMD_AT, reply=REPLY_AT):
                break
            time.sleep(0.5)
            timeout -= 500

        if timeout <= 0:  # no response to AT, last ditch attempt
            self._send_check_reply(CMD_AT, reply=REPLY_OK)
            time.sleep(0.1)
            self._send_check_reply(CMD_AT, reply=REPLY_OK)
            time.sleep(0.1)
            self._send_check_reply(CMD_AT, reply=REPLY_OK)
            time.sleep(0.1)

        # turn off echo
        self._send_check_reply(b"ATE0", reply=REPLY_OK)
        time.sleep(0.1)

        self._read_line()
        if not self._send_check_reply(b"ATE0", reply=REPLY_OK):
            return False

        # turn on hangupitude
        self._send_check_reply(b"AT+CVHU=0", reply=REPLY_OK)
        time.sleep(0.1)

        self._buf = b""
        self._uart.reset_input_buffer()

        self._uart_write(b"ATI\r\n")
        self._read_line(multiline=True)

        if self._buf.find(b"SIM808 R14") != -1:
            self._fona_type = FONA_808_V2
        elif self._buf.find(b"SIM808 R13") != -1:
            self._fona_type = FONA_808_V1
        elif self._buf.find(b"SIMCOM_SIM5320A") != -1:
            self._fona_type = FONA_3G_A
        elif self._buf.find(b"SIMCOM_SIM5320E") != -1:
            self._fona_type = FONA_3G_E

        if self._fona_type == FONA_800_L:
            # determine if SIM800H
            self._uart_write(b"AT+GMM\r\n")
            self._read_line(multiline=True)

            if self._buf.find(b"SIM800H") != -1:
                self._fona_type = FONA_800_H
        return True

    def factory_reset(self):
        """Resets modem to factory configuration."""
        self._uart_write(b"ATZ\r\n")

        if not self._expect_reply(REPLY_OK):
            return False
        return True

    def reset(self):
        """Performs a hardware reset on the modem."""
        if self._debug:
            print("* Reset FONA")
        self._rst.switch_to_output()
        self._rst.value = True
        time.sleep(0.01)
        self._rst.value = False
        time.sleep(0.1)
        self._rst.value = True

    @property
    # pylint: disable=too-many-return-statements
    def version(self):
        """The version of the FONA module. Can be FONA_800_L,
        FONA_800_H, FONA_808_V1, FONA_808_V2, FONA_3G_A, FONA3G_E.
        """
        return self._fona_type

    @property
    def iemi(self):
        """FONA Module's IEMI (International Mobile Equipment Identity) number."""
        if self._debug:
            print("FONA IEMI")
        self._uart.reset_input_buffer()

        self._uart_write(b"AT+GSN\r\n")
        self._read_line(multiline=True)
        iemi = self._buf[0:15]
        return iemi.decode("utf-8")

    @property
    def local_ip(self):
        """Module's local IP address, None if not set."""
        self._uart_write(b"AT+CIFSR\r\n")
        self._read_line()
        try:
            ip_addr = self.pretty_ip(self._buf)
        except ValueError:
            return None
        return ip_addr

    @property
    def iccid(self):
        """SIM Card's unique ICCID (Integrated Circuit Card Identifier)."""
        if self._debug:
            print("ICCID")
        self._uart_write(b"AT+CCID\r\n")
        self._read_line(timeout=2000)  # 6.2.23, 2sec max. response time
        iccid = self._buf.decode()
        return iccid

    @property
    def gprs(self):
        """GPRS (General Packet Radio Services) power status."""
        if not self._send_parse_reply(b"AT+CGATT?", b"+CGATT: ", ":"):
            return False
        if not self._buf:
            return False
        return True

    # pylint: disable=too-many-return-statements
    def set_gprs(self, apn=None, enable=True):
        """Configures and brings up GPRS.
        :param bool enable: Enables or disables GPRS.

        """
        if enable:
            apn_name, apn_user, apn_pass = apn

            # enable multi connection mode (3,1)
            if not self._send_check_reply(b"AT+CIPMUX=1", reply=REPLY_OK):
                return False
            self._read_line()

            # enable receive data manually (7,2)
            if not self._send_check_reply(b"AT+CIPRXGET=1", reply=REPLY_OK):
                return False

            # disconnect all sockets
            if not self._send_check_reply(
                b"AT+CIPSHUT", reply=b"SHUT OK", timeout=20000
            ):
                return False

            if not self._send_check_reply(b"AT+CGATT=1", reply=REPLY_OK, timeout=10000):
                return False

            # set bearer profile (APN)
            if not self._send_check_reply(
                b'AT+SAPBR=3,1,"CONTYPE","GPRS"', reply=REPLY_OK, timeout=10000
            ):
                return False

            # Send command AT+SAPBR=3,1,"APN","<apn value>"
            # where <apn value> is the configured APN value.
            self._send_check_reply_quoted(
                b'AT+SAPBR=3,1,"APN",', apn_name.encode(), REPLY_OK, 10000
            )

            # send AT+CSTT,"apn","user","pass"
            self._uart.reset_input_buffer()

            self._uart_write(b'AT+CSTT="' + apn_name.encode())

            if apn_user is not None:
                self._uart_write(b'","' + apn_user.encode())

            if apn_pass is not None:
                self._uart_write(b'","' + apn_pass.encode())
            self._uart_write(b'"\r\n')

            if not self._get_reply(REPLY_OK):
                return False

            # Set username
            if not self._send_check_reply_quoted(
                b'AT+SAPBR=3,1,"USER",', apn_user.encode(), REPLY_OK, 10000
            ):
                return False

            # Set password
            if not self._send_check_reply_quoted(
                b'AT+SAPBR=3,1,"PWD",', apn_pass.encode(), REPLY_OK, 100000
            ):
                return False

            # Open GPRS context
            if not self._send_check_reply(
                b"AT+SAPBR=1,1", reply=REPLY_OK, timeout=1850
            ):
                return False

            # Bring up wireless connection
            if not self._send_check_reply(b"AT+CIICR", reply=REPLY_OK, timeout=10000):
                return False

            if not self.local_ip:
                return False
        else:
            # reset PDP state
            if not self._send_check_reply(
                b"AT+CIPSHUT", reply=b"SHUT OK", timeout=20000
            ):
                return False

        return True

    @property
    def network_status(self):
        """The status of the cellular network."""
        self._read_line()
        if self._debug:
            print("Network status")
        if not self._send_parse_reply(b"AT+CREG?", b"+CREG: ", idx=1):
            return False
        status = self._buf
        if not 0 <= self._buf <= 5:
            status = -1
        return status

    @property
    def rssi(self):
        """The received signal strength indicator for the cellular network
        we are connected to.
        """
        if self._debug:
            print("RSSI")
        if not self._send_parse_reply(b"AT+CSQ", b"+CSQ: "):
            return False

        reply_num = self._buf
        rssi = 0
        if reply_num == 0:
            rssi = -115
        elif reply_num == 1:
            rssi = -111
        elif reply_num == 31:
            rssi = -52

        if 2 <= reply_num <= 30:
            rssi = map_range(reply_num, 2, 30, -110, -54)

        self._read_line()  # eat the 'ok'
        return rssi

    @property
    def gps(self):
        """Module's GPS status."""
        if self._debug:
            print("GPS Fix")
        if self._fona_type == FONA_808_V2:
            # 808 V2 uses GNS commands and doesn't have an explicit 2D/3D fix status.
            # Instead just look for a fix and if found assume it's a 3D fix.
            self._get_reply(b"AT+CGNSINF")

            if not b"+CGNSINF: " in self._buf:
                return False

            status = int(self._buf[10:11].decode("utf-8"))
            if status == 1:
                status = 3  # assume 3D fix
            self._read_line()
        else:
            raise NotImplementedError(
                "FONA 808 v1 not currently supported by this library."
            )
        return status

    @gps.setter
    def gps(self, gps_on=False):
        if not (
            self._fona_type == FONA_3G_A
            or self._fona_type == FONA_3G_E
            or self._fona_type == FONA_808_V1
            or self._fona_type == FONA_808_V2
        ):
            raise TypeError("GPS unsupported for this FONA module.")

        # check if already enabled or disabled
        if self._fona_type == FONA_808_V2:
            if not self._send_parse_reply(b"AT+CGPSPWR?", b"+CGPSPWR: ", ":"):
                return False
        self._read_line()
        if not self._send_parse_reply(b"AT+CGNSPWR?", b"+CGNSPWR: ", ":"):
            return False

        state = self._buf

        if gps_on and not state:
            self._read_line()
            if self._fona_type == FONA_808_V2:  # try GNS
                if not self._send_check_reply(b"AT+CGNSPWR=1", reply=REPLY_OK):
                    return False
            else:
                if not self._send_parse_reply(b"AT+CGPSPWR=1", reply_data=REPLY_OK):
                    return False
        else:
            if self._fona_type == FONA_808_V2:  # try GNS
                if not self._send_check_reply(b"AT+CGNSPWR=0", reply=REPLY_OK):
                    return False
                if not self._send_check_reply(b"AT+CGPSPWR=0", reply=REPLY_OK):
                    return False

        return True

    def pretty_ip(self, ip):  # pylint: disable=no-self-use, invalid-name
        """Converts a bytearray IP address to a dotted-quad string for printing"""
        return "%d.%d.%d.%d" % (ip[0], ip[1], ip[2], ip[3])

    def unpretty_ip(self, ip):  # pylint: disable=no-self-use, invalid-name
        """Converts a dotted-quad string to a bytearray IP address"""
        octets = [int(x) for x in ip.split(".")]
        return bytes(octets)

    ### SMS ###

    @property
    def enable_sms_notification(self):
        """Checks if SMS notifications are enabled."""
        if not self._send_parse_reply(b"AT+CNMI?\r\n", b"+CNMI:", idx=1):
            return False
        return self._buf

    @enable_sms_notification.setter
    def enable_sms_notification(self, enable=True):
        if enable:
            if not self._send_check_reply(b"AT+CNMI=2,1\r\n", reply=REPLY_OK):
                return False
        else:
            if not self._send_check_reply(b"AT+CNMI=2,0\r\n", reply=REPLY_OK):
                return False
        return True

    def receive_sms(self):
        """Checks for a message notification from the FONA module,
        replies back with the a tuple containing (sender, message).
        NOTE: This method needs to be polled consistently due to the lack
        of hw-based interrupts in CircuitPython.

        """
        if self._ri is not None:  # poll the RI pin
            if self._ri.value:
                return False, False
        if not self._uart.in_waiting:  # otherwise, poll the UART
            return False, False

        self._read_line()  # parse the rcv'd URC
        if not self._parse_reply(b"+CMTI: ", idx=1):
            return False, False
        slot = self._buf
        sender, message = self.read_sms(slot)

        if not self.delete_sms(slot):  # delete sms from module memory
            return False, False

        return sender, message.strip()

    def send_sms(self, phone_number, message):
        """Sends a message SMS to a phone number.
        :param int phone_number: Destination phone number.
        :param str message: Message to send to the phone number.

        """
        if not hasattr(phone_number, "to_bytes"):
            raise TypeError("Phone number must be integer")

        # select SMS message format, text mode (4.2.2)
        if not self._send_check_reply(b"AT+CMGF=1", reply=REPLY_OK):
            return False

        self._uart_write(b'AT+CMGS="+' + str(phone_number).encode() + b'"' + b"\r")
        self._read_line()

        if self._buf[0] != 62:  # expect '>'
            # promoting mark ('>') not found
            return False
        self._read_line()

        # write out message and ^z
        self._uart_write((message + chr(26)).encode())

        if self._fona_type == FONA_3G_A or self._fona_type == FONA_3G_E:
            self._read_line(200)  # eat first 'CRLF'
            self._read_line(200)  # eat second 'CRLF'

        # read +CMGS, wait ~10sec.
        self._read_line(10000)
        if not "+CMGS" in self._buf:
            return False

        if not self._expect_reply(REPLY_OK):
            return False
        return True

    def num_sms(self, sim_storage=True):
        """Returns the number of SMS messages stored in memory.
        :param bool sim_storage: SMS storage on the SIM, otherwise internal storage on FONA chip.

        """
        if not self._send_check_reply(b"AT+CMGF=1", reply=REPLY_OK):
            raise RuntimeError("Operating mode not supported by FONA module.")

        if sim_storage:  # ask how many SMS are stored
            if self._send_parse_reply(b"AT+CPMS?", FONA_SMS_STORAGE_SIM + b",", idx=1):
                return self._buf
        else:
            if self._send_parse_reply(
                b"AT+CPMS?", FONA_SMS_STORAGE_INTERNAL + b",", idx=1
            ):
                return self._buf

        self._read_line()  # eat OK
        if self._send_parse_reply(b"AT+CPMS?", b'"SM",', idx=1):
            return self._buf

        self._read_line()  # eat OK
        if self._send_parse_reply(b"AT+CPMS?", b'"SM_P",', idx=1):
            return self._buf
        return 0

    def delete_sms(self, sms_slot):
        """Deletes a SMS message from a storage (internal or sim) slot
        :param int sms_slot: SMS SIM or FONA memory slot number.

        """
        if not self._send_check_reply(b"AT+CMGF=1", reply=REPLY_OK):
            return False

        if not self._send_check_reply(
            b"AT+CMGD=" + str(sms_slot).encode(), reply=REPLY_OK
        ):
            return False

        return True

    def delete_all_sms(self):
        """Deletes all SMS messages on the FONA SIM."""
        self._read_line()
        if not self._send_check_reply(b"AT+CMGF=1", reply=REPLY_OK):
            return False

        if self._fona_type == FONA_3G_A or self._fona_type == FONA_3G_E:
            num_sms = self.num_sms()
            for slot in range(0, num_sms):
                if not self.delete_sms(slot):
                    return False
        else:  # DEL ALL on 808
            if not self._send_check_reply(
                b'AT+CMGDA="DEL ALL"', reply=REPLY_OK, timeout=25000
            ):
                return False
        return True

    def read_sms(self, sms_slot):
        """Reads and parses SMS messages from FONA device. Returns the SMS
        sender's phone number and the message contents as a tuple.
        :param int sms_slot: SMS SIM or FONA memory slot number.

        """
        if not self._send_check_reply(b"AT+CMGF=1", reply=REPLY_OK):
            return False
        if not self._send_check_reply(b"AT+CSDH=1", reply=REPLY_OK):
            return False

        self._uart_write(b"AT+CMGR=" + str(sms_slot).encode() + b"\r\n")
        self._read_line(1000)
        resp = self._buf

        # get sender
        if not self._parse_reply(b"+CMGR:", idx=1):
            return False
        sender = self._buf.strip('"')

        # get sms length
        self._buf = resp
        if not self._parse_reply(b"+CMGR:", idx=11):
            return False
        sms_len = self._buf

        self._buf = bytearray(sms_len)
        self._uart.readinto(self._buf)
        message = bytes(self._buf).decode()
        self._uart.reset_input_buffer()
        self._read_line()  # eat 'OK'

        return sender, message

    ### Socket API (TCP, UDP) ###

    def get_host_by_name(self, hostname):
        """Converts a hostname to a packed 4-byte IP address.
        :param str hostname: Destination server.

        """
        self._read_line()
        if self._debug:
            print("*** Get host by name")
        if isinstance(hostname, str):
            hostname = bytes(hostname, "utf-8")

        if not self._send_check_reply(
            b'AT+CDNSGIP="' + hostname + b'"\r\n', reply=REPLY_OK
        ):
            return False

        self._read_line()
        while not self._parse_reply(b"+CDNSGIP:", idx=2):
            self._read_line()
        return self._buf

    def get_socket(self):
        """Obtains a socket, if available."""
        if self._debug:
            print("*** Get socket")

        self._uart_write(b"AT+CIPSTATUS\r\n")
        self._read_line(100)  # OK
        self._read_line(100)  # table header

        allocated_socket = 0
        for sock in range(0, FONA_MAX_SOCKETS):  # check if INITIAL state
            self._read_line(100)
            self._parse_reply(b"C:", idx=5)
            if self._buf.strip('"') == "INITIAL" or self._buf.strip('"') == "CLOSED":
                allocated_socket = sock
                break
        # read out the rest of the responses
        for _ in range(allocated_socket, FONA_MAX_SOCKETS):
            self._read_line(100)
        if self._debug:
            print("Allocated socket #%d" % allocated_socket)
        return allocated_socket

    def remote_ip(self, sock_num):
        """Returns the IP address of the remote server.
        :param int sock_num: Desired socket.

        """
        assert (
            sock_num < FONA_MAX_SOCKETS
        ), "Provided socket exceeds the maximum number of \
                                             sockets for the FONA module."
        self._uart_write(b"AT+CIPSTATUS=" + str(sock_num).encode() + b"\r\n")
        self._read_line(100)

        self._parse_reply(b"+CIPSTATUS:", idx=3)
        return self._buf

    def socket_status(self, sock_num):
        """Returns the socket connection status, False if not connected.
        :param int sock_num: Desired socket number.

        """
        assert (
            sock_num < FONA_MAX_SOCKETS
        ), "Provided socket exceeds the maximum number of \
                                             sockets for the FONA module."
        if not self._send_check_reply(b"AT+CIPSTATUS", reply=REPLY_OK, timeout=100):
            return False
        self._read_line()

        for state in range(0, sock_num + 1):  # read "C: <n>" for each active connection
            self._read_line()
            if state == sock_num:
                break
        self._parse_reply(b"C:", idx=5)

        state = self._buf

        # eat the rest of the sockets
        for _ in range(sock_num, FONA_MAX_SOCKETS):
            self._read_line()

        if not "CONNECTED" in state:
            return False

        return True

    def socket_available(self, sock_num):
        """Returns the amount of bytes available to be read from the socket.
        :param int sock_num: Desired socket to return bytes available from.

        """
        assert (
            sock_num < FONA_MAX_SOCKETS
        ), "Provided socket exceeds the maximum number of \
                                             sockets for the FONA module."
        if not self._send_parse_reply(
            b"AT+CIPRXGET=4," + str(sock_num).encode(),
            b"+CIPRXGET: 4," + str(sock_num).encode() + b",",
        ):
            return False
        data = self._buf
        if self._debug:
            print("\t {} bytes available.".format(self._buf))

        self._read_line()
        self._read_line()

        return data

    def socket_connect(self, sock_num, dest, port, conn_mode=TCP_MODE):
        """Connects to a destination IP address or hostname.
        By default, we use conn_mode TCP_MODE but we may also use UDP_MODE.
        :param int sock_num: Desired socket number
        :param str dest: Destination dest address.
        :param int port: Destination dest port.
        :param int conn_mode: Connection mode (TCP/UDP)

        """
        if self._debug:
            print(
                "*** Socket connect, protocol={}, port={}, ip={}".format(
                    conn_mode, port, dest
                )
            )

        self._uart.reset_input_buffer()
        assert (
            sock_num < FONA_MAX_SOCKETS
        ), "Provided socket exceeds the maximum number of \
                                             sockets for the FONA module."

        # Query local IP Address
        self._uart_write(b"AT+CIFSR\r\n")
        self._read_line()

        # Start connection
        self._uart_write(b"AT+CIPSTART=" + str(sock_num).encode())
        if conn_mode == 0:
            self._uart_write(b',"TCP","')
        else:
            self._uart_write(b',"UDP","')
        self._uart_write(dest.encode() + b'","' + str(port).encode() + b'"\r\n')

        if not self._expect_reply(REPLY_OK):
            return False

        if not self._expect_reply(b"CONNECT OK"):
            return False
        return True

    def socket_close(self, sock_num):
        """Close TCP or UDP connection
        :param int sock_num: Desired socket number.

        """
        if self._debug:
            print("*** Closing socket #%d" % sock_num)
        assert (
            sock_num < FONA_MAX_SOCKETS
        ), "Provided socket exceeds the maximum number of \
                                             sockets for the FONA module."

        self._uart_write(b"AT+CIPCLOSE=" + str(sock_num).encode() + b"\r\n")
        self._read_line(3000)

        if self._fona_type == FONA_3G_A or self._fona_type == FONA_3G_E:
            if not self._expect_reply(REPLY_OK):
                return False
        else:
            if not self._expect_reply(b"CLOSE OK"):
                return False
        return True

    def socket_read(self, sock_num, length):
        """Read data from the network into a buffer.
        Returns buffer and amount of bytes read.
        :param int sock_num: Desired socket to read from.
        :param int length: Desired length to read.

        """
        self._read_line()
        assert (
            sock_num < FONA_MAX_SOCKETS
        ), "Provided socket exceeds the maximum number of \
                                             sockets for the FONA module."
        if self._debug:
            print("* socket read")

        self._uart_write(b"AT+CIPRXGET=2," + str(sock_num).encode() + b",")
        self._uart_write(str(length).encode() + b"\r\n")
        self._read_line()

        if not self._parse_reply(b"+CIPRXGET:"):
            return False

        return self._uart.read(length)

    def socket_write(self, sock_num, buffer, timeout=3000):
        """Writes bytes to the socket.
        :param int sock_num: Desired socket number to write to.
        :param bytes buffer: Bytes to write to socket.
        :param int timeout: Socket write timeout, in milliseconds.

        """
        self._read_line()
        assert (
            sock_num < FONA_MAX_SOCKETS
        ), "Provided socket exceeds the maximum number of \
                                             sockets for the FONA module."

        self._uart.reset_input_buffer()
        self._uart_write(b"AT+CIPSEND=" + str(sock_num).encode())
        self._uart_write(b"," + str(len(buffer)).encode() + b"\r\n")
        self._read_line()

        if self._buf[0] != 62:
            # promoting mark ('>') not found
            return False

        self._uart_write(buffer + b"\r\n")
        self._read_line(timeout)

        if "SEND OK" not in self._buf.decode():
            return False

        return True

    ### UART Reply/Response Helpers ###

    def _uart_write(self, buffer):
        """UART ``write`` with optional debug that prints
        the buffer before sending.
        :param bytes buffer: Buffer of bytes to send to the bus.

        """
        if self._debug:
            print("\tUARTWRITE ::", buffer.decode())
        self._uart.write(buffer)

    def _send_parse_reply(self, send_data, reply_data, divider=",", idx=0):
        """Sends data to FONA module, parses reply data returned.
        :param bytes send_data: Data to send to the module.
        :param bytes send_data: Data received by the FONA module.
        :param str divider: Separator

        """
        self._read_line()
        self._get_reply(send_data)

        if not self._parse_reply(reply_data, divider, idx):
            return False
        return True

    def _get_reply(
        self, data=None, prefix=None, suffix=None, timeout=FONA_DEFAULT_TIMEOUT_MS
    ):
        """Send data to FONA, read response into buffer.
        :param bytes data: Data to send to FONA module.
        :param int timeout: Time to wait for UART response.

        """
        self._uart.reset_input_buffer()

        if data is not None:
            self._uart_write(data + b"\r\n")
        else:
            self._uart_write(prefix + suffix + b"\r\n")

        return self._read_line(timeout)

    def _parse_reply(self, reply, divider=",", idx=0):
        """Attempts to find reply in UART buffer, reads up to divider.
        :param bytes reply: Expected response from FONA module.
        :param str divider: Divider character.

        """
        parsed_reply = self._buf.find(reply)
        if parsed_reply == -1:
            return False
        parsed_reply = self._buf[parsed_reply:]

        parsed_reply = self._buf[len(reply) :]
        parsed_reply = parsed_reply.decode("utf-8")

        parsed_reply = parsed_reply.split(divider)
        parsed_reply = parsed_reply[idx]

        try:
            self._buf = int(parsed_reply)
        except ValueError:
            self._buf = parsed_reply

        return True

    def _read_line(self, timeout=FONA_DEFAULT_TIMEOUT_MS, multiline=False):
        """Reads one or multiple lines into the buffer. Optionally prints the buffer
        after reading.
        :param int timeout: Time to wait for UART serial to reply, in seconds.
        :param bool multiline: Read multiple lines.

        """
        self._buf = b""
        reply_idx = 0
        while timeout:
            if reply_idx >= 254:
                break

            while self._uart.in_waiting:
                char = self._uart.read(1)
                if char == b"\r":
                    continue
                if char == b"\n":
                    if reply_idx == 0:  # ignore first '\n'
                        continue
                    if not multiline:  # second '\n' is EOL
                        timeout = 0
                        break
                self._buf += char
                reply_idx += 1

            if timeout == 0:
                break
            timeout -= 1
            time.sleep(0.001)

        if self._debug:
            print("\tUARTREAD ::", self._buf.decode())

        return reply_idx, self._buf

    def _send_check_reply(
        self,
        send=None,
        prefix=None,
        suffix=None,
        reply=None,
        timeout=FONA_DEFAULT_TIMEOUT_MS,
    ):
        """Sends data to FONA, validates response.
        :param bytes send: Command.
        :param bytes reply: Expected response from module.

        """
        self._read_line()
        if send is None:
            if not self._get_reply(prefix=prefix, suffix=suffix, timeout=timeout):
                return False
        else:
            if not self._get_reply(send, timeout=timeout):
                return False

        if not self._buf == reply:
            return False

        return True

    def _send_check_reply_quoted(
        self, prefix, suffix, reply, timeout=FONA_DEFAULT_TIMEOUT_MS
    ):
        """Send prefix, ", suffix, ", and a newline. Verify response against reply.
        :param bytes prefix: Command prefix.
        :param bytes prefix: Command ", suffix, ".
        :param bytes reply: Expected response from module.
        :param int timeout: Time to expect reply back from FONA, in milliseconds.

        """
        self._buf = b""

        self._get_reply_quoted(prefix, suffix, timeout)

        if reply not in self._buf:
            return False
        return True

    def _get_reply_quoted(self, prefix, suffix, timeout):
        """Send prefix, ", suffix, ", and newline.
        Returns: Response (and also fills buffer with response).
        :param bytes prefix: Command prefix.
        :param bytes prefix: Command ", suffix, ".
        :param int timeout: Time to expect reply back from FONA, in milliseconds.

        """
        self._uart.reset_input_buffer()

        self._uart_write(prefix + b'"' + suffix + b'"\r\n')

        return self._read_line(timeout)

    def _expect_reply(self, reply, timeout=10000):
        """Reads line from FONA module and compares to reply from FONA module.
        :param bytes reply: Expected reply from module.

        """
        self._read_line(timeout)
        if reply not in self._buf:
            return False
        return True
