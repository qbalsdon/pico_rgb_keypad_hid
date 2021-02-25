# SPDX-FileCopyrightText: 2019 ladyada for Adafruit Industries
# SPDX-FileCopyrightText: 2020 Brent Rubell for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_fona_socket`
================================================================================

A socket compatible interface with the Adafruit FONA cellular module.

* Author(s): ladyada, Brent Rubell

"""
import gc
import time
from micropython import const

_the_interface = None  # pylint: disable=invalid-name


def set_interface(iface):
    """Helper to set the global internet interface."""
    global _the_interface  # pylint: disable=global-statement, invalid-name
    _the_interface = iface


def htonl(x):
    """Convert 32-bit positive integers from host to network byte order."""
    return (
        ((x) << 24 & 0xFF000000)
        | ((x) << 8 & 0x00FF0000)
        | ((x) >> 8 & 0x0000FF00)
        | ((x) >> 24 & 0x000000FF)
    )


def htons(x):
    """Convert 16-bit positive integers from host to network byte order."""
    return (((x) << 8) & 0xFF00) | (((x) >> 8) & 0xFF)


SOCK_STREAM = const(0x00)  # TCP
TCP_MODE = 80
SOCK_DGRAM = const(0x01)  # UDP
AF_INET = const(3)
NO_SOCKET_AVAIL = const(255)

# keep track of sockets we allocate
SOCKETS = []

# pylint: disable=too-many-arguments, unused-argument
def getaddrinfo(host, port, family=0, socktype=0, proto=0, flags=0):
    """Translate the host/port argument into a sequence of 5-tuples that
    contain all the necessary arguments for creating a socket connected to that service.
    """
    if not isinstance(port, int):
        raise RuntimeError("Port must be an integer")
    return [(AF_INET, socktype, proto, "", (gethostbyname(host), port))]


def gethostbyname(hostname):
    """Translate a host name to IPv4 address format. The IPv4 address
    is returned as a string.
    :param str hostname: Desired hostname.
    """
    addr = _the_interface.get_host_by_name(hostname)
    return addr.strip('"')


# pylint: disable=invalid-name, redefined-builtin
class socket:
    """A simplified implementation of the Python 'socket' class
    for connecting to a FONA cellular module.
    :param int family: Socket address (and protocol) family.
    :param int type: Socket type.

    """

    def __init__(
        self, family=AF_INET, type=SOCK_STREAM, proto=0, fileno=None, socknum=None
    ):
        if family != AF_INET:
            raise RuntimeError("Only AF_INET family supported by cellular sockets.")
        self._sock_type = type
        self._buffer = b""
        if hasattr(_the_interface, "tx_timeout"):
            self._timeout = _the_interface.tx_timeout
        else:
            self._timeout = 3000  # FONA800

        self._socknum = _the_interface.get_socket()
        SOCKETS.append(self._socknum)
        self.settimeout(self._timeout)

    @property
    def socknum(self):
        """Returns the socket object's socket number."""
        return self._socknum

    @property
    def connected(self):
        """Returns whether or not we are connected to the socket."""
        return _the_interface.socket_status(self.socknum)

    def getpeername(self):
        """Return the remote address to which the socket is connected."""
        return _the_interface.remote_ip(self.socknum)

    def inet_aton(self, ip_string):
        """Convert an IPv4 address from dotted-quad string format.
        :param str ip_string: IP Address, as a dotted-quad string.

        """
        self._buffer = b""
        self._buffer = [int(item) for item in ip_string.split(".")]
        self._buffer = bytearray(self._buffer)
        return self._buffer

    def connect(self, address, conn_mode=None):
        """Connect to a remote socket at address. (The format of address depends
        on the address family — see above.)
        :param tuple address: Remote socket as a (host, port) tuple.
        :param int conn_mode: Connection mode (TCP/UDP)

        """
        assert (
            conn_mode != 0x03
        ), "Error: SSL/TLS is not currently supported by CircuitPython."
        host, port = address

        if not _the_interface.socket_connect(
            self.socknum, host, port, conn_mode=self._sock_type
        ):
            raise RuntimeError("Failed to connect to host", host)
        self._buffer = b""

    def send(self, data):
        """Send data to the socket. The socket must be connected to
        a remote socket prior to calling this method.
        :param bytes data: Desired data to send to the socket.

        """
        _the_interface.socket_write(self._socknum, data, self._timeout)
        gc.collect()

    def recv(self, bufsize=0):
        """Reads some bytes from the connected remote address.
        :param int bufsize: maximum number of bytes to receive
        """
        # print("Socket read", bufsize)
        if bufsize == 0:  # read as much as we can at the moment
            while True:
                avail = self.available()
                if avail:
                    self._buffer += _the_interface.socket_read(self._socknum, avail)
                else:
                    break
            gc.collect()
            ret = self._buffer
            self._buffer = b""
            gc.collect()
            return ret
        stamp = time.monotonic()

        to_read = bufsize - len(self._buffer)
        received = []
        while to_read > 0:
            # print("Bytes to read:", to_read)
            avail = self.available()
            if avail:
                stamp = time.monotonic()
                recv = _the_interface.socket_read(self._socknum, min(to_read, avail))
                received.append(recv)
                to_read -= len(recv)
                gc.collect()
            if self._timeout > 0 and time.monotonic() - stamp > self._timeout:
                break
        # print(received)
        self._buffer += b"".join(received)

        ret = None
        if len(self._buffer) == bufsize:
            ret = self._buffer
            self._buffer = b""
        else:
            ret = self._buffer[:bufsize]
            self._buffer = self._buffer[bufsize:]
        gc.collect()
        return ret

    def readline(self):
        """Attempt to return as many bytes as we can up to but not including '\r\n'"""
        # print("Socket readline")
        stamp = time.monotonic()
        while b"\r\n" not in self._buffer:
            # there's no line already in there, read some more
            avail = self.available()
            if avail:
                self._buffer += _the_interface.socket_read(self._socknum, avail)
            elif self._timeout > 0 and time.monotonic() - stamp > self._timeout:
                self.close()  # Make sure to close socket so that we don't exhaust sockets.
                raise RuntimeError("Didn't receive full response, failing out")
        firstline, self._buffer = self._buffer.split(b"\r\n", 1)
        gc.collect()
        return firstline

    def available(self):
        """Returns how many bytes are available to be read from the socket."""
        return _the_interface.socket_available(self._socknum)

    def settimeout(self, value):
        """Sets socket read timeout.
        :param int value: Socket read timeout, in seconds.

        """
        if value < 0:
            raise Exception("Timeout period should be non-negative.")
        self._timeout = value

    def gettimeout(self):
        """Return the timeout in seconds (float) associated
        with socket operations, or None if no timeout is set.

        """
        return self._timeout

    def close(self):
        """Closes the socket."""
        return _the_interface.socket_close(self._socknum)
