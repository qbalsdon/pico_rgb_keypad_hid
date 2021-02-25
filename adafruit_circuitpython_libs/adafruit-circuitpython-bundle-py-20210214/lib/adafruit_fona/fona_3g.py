# SPDX-FileCopyrightText: Limor Fried/Ladyada for Adafruit Industries
# SPDX-FileCopyrightText: 2020 Brent Rubell for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
:py:class:`~adafruit_fona.fona_3g.FONA3G`
`adafruit_fona_3g`
================================================================================

FONA3G cellular module instance.

* Author(s): ladyada, Brent Rubell

Implementation Notes
--------------------

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://github.com/adafruit/circuitpython/releases

"""
from micropython import const
from .adafruit_fona import FONA, REPLY_OK

__version__ = "2.1.2"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_FONA.git"

FONA_MAX_SOCKETS = const(10)


class FONA3G(FONA):
    """FONA 3G module interface.
    :param ~busio.uart UART: FONA UART connection.
    :param ~digialio RST: FONA RST pin.
    :param ~digialio RI: Optional FONA Ring Interrupt (RI) pin.
    :param bool debug: Enable debugging output.

    """

    def __init__(self, uart, rst, ri=None, debug=False):
        uart.baudrate = 4800
        super().__init__(uart, rst, ri, debug)

    def set_baudrate(self, baudrate):
        """Sets the FONA's UART baudrate."""
        if not self._send_check_reply(
            b"AT+IPREX=" + str(baudrate).encode(), reply=REPLY_OK
        ):
            return False
        return True

    @property
    def gps(self):
        """Module's GPS status."""
        if not self._send_check_reply(b"AT+CGPS?", reply=b"+CGPS: 1,1"):
            return False
        return True

    @gps.setter
    def gps(self, gps_on=False):
        # check if GPS is already enabled
        if not self._send_parse_reply(b"AT+CGPS?", b"+CGPS: "):
            return False

        state = self._buf

        if gps_on and not state:
            self._read_line()
            if not self._send_check_reply(b"AT+CGPS=1", reply=REPLY_OK):
                return False
        else:
            if not self._send_check_reply(b"AT+CGPS=0", reply=REPLY_OK):
                return False
            self._read_line(2000)  # eat '+CGPS: 0'
        return True

    @property
    def ue_system_info(self):
        """UE System status."""
        self._send_parse_reply(b"AT+CPSI?\r\n", b"+CPSI: ")
        if not self._buf == "GSM" or self._buf == "WCDMA":  # 5.15
            return False
        return True

    @property
    def local_ip(self):
        """Module's local IP address, None if not set."""
        if not self._send_parse_reply(b"AT+IPADDR", b"+IPADDR:"):
            return None
        return self._buf

    # pylint: disable=too-many-return-statements
    def set_gprs(self, apn=None, enable=True):
        """Configures and brings up GPRS.
        :param bool enable: Enables or disables GPRS.

        """
        if enable:
            if not self._send_check_reply(b"AT+CGATT=1", reply=REPLY_OK, timeout=10000):
                return False

            if apn is not None:  # Configure APN
                apn_name, apn_user, apn_pass = apn
                if not self._send_check_reply_quoted(
                    b'AT+CGSOCKCONT=1,"IP",', apn_name.encode(), REPLY_OK, 10000
                ):
                    return False

                if apn_user is not None:
                    self._uart_write(b"AT+CGAUTH=1,1,")
                    self._uart_write(b'"' + apn_pass.encode() + b'"')
                    self._uart_write(b',"' + apn_user.encode() + b'"\r\n')

            if not self._get_reply(REPLY_OK, timeout=10000):
                return False

            # Enable PDP Context
            if not self._send_check_reply(
                b"AT+CIPMODE=1", reply=REPLY_OK, timeout=10000
            ):  # Transparent mode
                return False

            # Open network
            if not self._send_check_reply(
                b"AT+NETOPEN=,,1", reply=b"Network opened", timeout=120000
            ):
                return False
            self._read_line()

            if not self.local_ip:
                return True
        else:
            # reset PDP state
            if not self._send_check_reply(
                b"AT+NETCLOSE", reply=b"Network closed", timeout=20000
            ):
                return False
        return True

    ### Socket API (TCP, UDP) ###

    @property
    def tx_timeout(self):
        """CIPSEND timeout, in milliseconds."""
        self._read_line()
        if not self._send_parse_reply(b"AT+CIPTIMEOUT?", b"+CIPTIMEOUT:", idx=2):
            return False
        return True

    @tx_timeout.setter
    def tx_timeout(self, timeout):
        self._read_line()
        if not self._send_check_reply(
            b"AT+CIPTIMEOUT=" + str(timeout).encode(), reply=REPLY_OK
        ):
            return False
        return True

    def get_host_by_name(self, hostname):
        """Converts a hostname to a 4-byte IP address.
        :param str hostname: Domain name.
        """
        self._read_line()
        if self._debug:
            print("*** Get host by name")
        if isinstance(hostname, str):
            hostname = bytes(hostname, "utf-8")

        self._uart_write(b'AT+CDNSGIP="' + hostname + b'"\r\n')
        self._read_line(10000)  # Read the +CDNSGIP, takes a while

        if not self._parse_reply(b"+CDNSGIP: ", idx=2):
            return False
        return self._buf

    def get_socket(self):
        """Returns an unused socket."""
        if self._debug:
            print("*** Get socket")

        self._read_line()
        self._uart_write(b"AT+CIPOPEN?\r\n")  # Query which sockets are busy

        socket = 0
        for socket in range(0, FONA_MAX_SOCKETS):
            self._read_line(120000)
            try:  # SIMCOM5320 lacks a socket connection status, this is a workaround
                self._parse_reply(b"+CIPOPEN: ", idx=1)
            except IndexError:
                break

        for _ in range(socket, FONA_MAX_SOCKETS):
            self._read_line()  # eat the rest of '+CIPOPEN' responses

        if self._debug:
            print("Allocated socket #%d" % socket)
        return socket

    def socket_connect(self, sock_num, dest, port, conn_mode=0):
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
        self._send_check_reply(b"AT+CIPHEAD=0", reply=REPLY_OK)  # do not show ip header
        self._send_check_reply(
            b"AT+CIPSRIP=0", reply=REPLY_OK
        )  # do not show remote ip/port
        self._send_check_reply(b"AT+CIPRXGET=1", reply=REPLY_OK)  # manually get data

        self._uart_write(b"AT+CIPOPEN=" + str(sock_num).encode())
        if conn_mode == 0:
            self._uart_write(b',"TCP","')
        else:
            self._uart_write(b',"UDP","')
        self._uart_write(dest.encode() + b'",' + str(port).encode() + b"\r\n")

        if not self._expect_reply(b"Connect ok"):
            return False
        return True

    def remote_ip(self, sock_num):
        """Returns the IP address of the remote connection."""
        self._read_line()
        assert (
            sock_num < FONA_MAX_SOCKETS
        ), "Provided socket exceeds the maximum number of \
                                             sockets for the FONA module."

        self._uart_write(b"AT+CIPOPEN?\r\n")
        for _ in range(0, sock_num + 1):
            self._read_line()
            self._parse_reply(b"+CIPOPEN:", idx=2)
        ip_addr = self._buf

        for _ in range(sock_num, FONA_MAX_SOCKETS):
            self._read_line()  # eat the rest of '+CIPOPEN' responses
        return ip_addr

    def socket_write(self, sock_num, buffer, timeout=120000):
        """Writes len(buffer) bytes to the socket.
        :param int sock_num: Desired socket number to write to.
        :param bytes buffer: Bytes to write to socket.
        :param int timeout: Socket write timeout, in milliseconds. Defaults to 120000ms.

        """
        self._read_line()
        assert (
            sock_num < FONA_MAX_SOCKETS
        ), "Provided socket exceeds the maximum number of \
                                             sockets for the FONA module."

        self._uart.reset_input_buffer()

        self._uart_write(
            b"AT+CIPSEND="
            + str(sock_num).encode()
            + b","
            + str(len(buffer)).encode()
            + b"\r\n"
        )
        self._read_line()
        if self._buf[0] != 62:
            # promoting mark ('>') not found
            return False

        self._uart_write(buffer + b"\r\n")
        self._read_line()  # eat 'OK'

        self._read_line(3000)  # expect +CIPSEND: rx,tx
        if not self._parse_reply(b"+CIPSEND:", idx=1):
            return False
        if not self._buf == len(buffer):  # assert data sent == buffer size
            return False

        self._read_line(timeout)
        if "Send ok" not in self._buf.decode():
            return False
        return True

    def socket_status(self, sock_num):
        """Returns socket status, True if connected. False otherwise.
        :param int sock_num: Desired socket number.

        """
        if not self._send_parse_reply(b"AT+CIPCLOSE?", b"+CIPCLOSE:", idx=sock_num):
            return False
        if not self._buf == 1:
            return False
        return True
