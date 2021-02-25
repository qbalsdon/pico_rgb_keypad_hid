# SPDX-FileCopyrightText: 2019 ladyada for Adafruit Industries
# SPDX-FileCopyrightText: 2020 Brent Rubell for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_wiznet5k_socket`
================================================================================

A socket compatible interface with the Wiznet5k module.

* Author(s): ladyada, Brent Rubell, Patrick Van Oosterwijck, Adam Cummick

"""
import gc
import time
from micropython import const
from adafruit_wiznet5k import adafruit_wiznet5k

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


SOCK_STREAM = const(0x21)  # TCP
TCP_MODE = 80
SOCK_DGRAM = const(0x02)  # UDP
AF_INET = const(3)
SOCKET_INVALID = const(255)


# pylint: disable=too-many-arguments, unused-argument
def getaddrinfo(host, port, family=0, socktype=0, proto=0, flags=0):
    """Translate the host/port argument into a sequence of 5-tuples that
    contain all the necessary arguments for creating a socket connected to that service.

    """
    if not isinstance(port, int):
        raise RuntimeError("Port must be an integer")
    if is_ipv4(host):
        return [(AF_INET, socktype, proto, "", (host, port))]
    return [(AF_INET, socktype, proto, "", (gethostbyname(host), port))]


def gethostbyname(hostname):
    """Translate a host name to IPv4 address format. The IPv4 address
    is returned as a string.
    :param str hostname: Desired hostname.
    """
    addr = _the_interface.get_host_by_name(hostname)
    addr = "{}.{}.{}.{}".format(addr[0], addr[1], addr[2], addr[3])
    return addr


def is_ipv4(host):
    """Checks if a host string is an IPv4 address.
    :param str host: host's name or ip
    """
    octets = host.split(".", 3)
    if len(octets) != 4 or not "".join(octets).isdigit():
        return False
    for octet in octets:
        if int(octet) > 255:
            return False
    return True


# pylint: disable=invalid-name, too-many-public-methods
class socket:
    """A simplified implementation of the Python 'socket' class
    for connecting to a Wiznet5k module.
    :param int family: Socket address (and protocol) family.
    :param int type: Socket type.

    """

    # pylint: disable=redefined-builtin,unused-argument
    def __init__(
        self, family=AF_INET, type=SOCK_STREAM, proto=0, fileno=None, socknum=None
    ):
        if family != AF_INET:
            raise RuntimeError("Only AF_INET family supported by W5K modules.")
        self._sock_type = type
        self._buffer = b""
        self._timeout = 0
        self._listen_port = None

        self._socknum = _the_interface.get_socket()
        if self._socknum == SOCKET_INVALID:
            raise RuntimeError("Failed to allocate socket.")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._sock_type == SOCK_STREAM:
            self.disconnect()
            stamp = time.monotonic()
            while self.status == adafruit_wiznet5k.SNSR_SOCK_FIN_WAIT:
                if time.monotonic() - stamp > 1000:
                    raise RuntimeError("Failed to disconnect socket")
        self.close()
        stamp = time.monotonic()
        while self.status != adafruit_wiznet5k.SNSR_SOCK_CLOSED:
            if time.monotonic() - stamp > 1000:
                raise RuntimeError("Failed to close socket")

    @property
    def socknum(self):
        """Returns the socket object's socket number."""
        return self._socknum

    @property
    def status(self):
        """Returns the status of the socket"""
        return _the_interface.socket_status(self.socknum)[0]

    @property
    def connected(self):
        """Returns whether or not we are connected to the socket."""
        if self.socknum >= _the_interface.max_sockets:
            return False
        status = _the_interface.socket_status(self.socknum)[0]
        if status == adafruit_wiznet5k.SNSR_SOCK_CLOSE_WAIT and self.available() == 0:
            result = False
        else:
            result = status not in (
                adafruit_wiznet5k.SNSR_SOCK_CLOSED,
                adafruit_wiznet5k.SNSR_SOCK_LISTEN,
                adafruit_wiznet5k.SNSR_SOCK_TIME_WAIT,
                adafruit_wiznet5k.SNSR_SOCK_FIN_WAIT,
            )
        if not result and status != adafruit_wiznet5k.SNSR_SOCK_LISTEN:
            self.close()
        return result

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

    def bind(self, address):
        """Bind the socket to the listen port, if host is specified the interface
        will be reconfigured to that IP.
        :param tuple address: local socket as a (host, port) tuple.
        """
        if address[0] is not None:
            ip_address = _the_interface.unpretty_ip(address[0])
            current_ip, subnet_mask, gw_addr, dns = _the_interface.ifconfig
            if ip_address != current_ip:
                _the_interface.ifconfig = (ip_address, subnet_mask, gw_addr, dns)
        self._listen_port = address[1]

    def listen(self, backlog=None):
        """Listen on the port specified by bind.
        :param backlog: For compatibility but ignored.
        """
        assert self._listen_port is not None, "Use bind to set the port before listen!"
        _the_interface.socket_listen(self.socknum, self._listen_port)
        self._buffer = b""

    def accept(self):
        """Accept a connection. The socket must be bound to an address and listening for
        connections. The return value is a pair (conn, address) where conn is a new
        socket object usable to send and receive data on the connection, and address is
        the address bound to the socket on the other end of the connection.
        """
        stamp = time.monotonic()
        while self.status not in (
            adafruit_wiznet5k.SNSR_SOCK_SYNRECV,
            adafruit_wiznet5k.SNSR_SOCK_ESTABLISHED,
        ):
            if self._timeout > 0 and time.monotonic() - stamp > self._timeout:
                return None
            if self.status == adafruit_wiznet5k.SNSR_SOCK_CLOSED:
                self.close()
                self.listen()

        new_listen_socknum, addr = _the_interface.socket_accept(self.socknum)
        current_socknum = self.socknum
        # Create a new socket object and swap socket nums so we can continue listening
        client_sock = socket()
        client_sock._socknum = current_socknum  # pylint: disable=protected-access
        self._socknum = new_listen_socknum  # pylint: disable=protected-access
        self.bind((None, self._listen_port))
        self.listen()
        while self.status != adafruit_wiznet5k.SNSR_SOCK_LISTEN:
            raise RuntimeError("Failed to open new listening socket")
        return client_sock, addr

    def connect(self, address, conntype=None):
        """Connect to a remote socket at address.
        :param tuple address: Remote socket as a (host, port) tuple.
        """
        assert (
            conntype != 0x03
        ), "Error: SSL/TLS is not currently supported by CircuitPython."
        host, port = address

        if hasattr(host, "split"):
            try:
                host = tuple(map(int, host.split(".")))
            except ValueError:
                host = _the_interface.get_host_by_name(host)
        if not _the_interface.socket_connect(
            self.socknum, host, port, conn_mode=self._sock_type
        ):
            raise RuntimeError("Failed to connect to host", host)
        self._buffer = b""

    def send(self, data):
        """Send data to the socket. The socket must be connected to
        a remote socket.
        :param bytearray data: Desired data to send to the socket.
        """
        _the_interface.socket_write(self.socknum, data, self._timeout)
        gc.collect()

    def sendto(self, data, address):
        """Send data to the socket. The socket must be connected to
        a remote socket.
        :param bytearray data: Desired data to send to the socket.
        :param tuple address: Remote socket as a (host, port) tuple.
        """
        self.connect(address)
        return self.send(data)

    def recv(self, bufsize=0, flags=0):  # pylint: disable=too-many-branches
        """Reads some bytes from the connected remote address.
        :param int bufsize: Maximum number of bytes to receive.
        :param int flags: ignored, present for compatibility.
        """
        # print("Socket read", bufsize)
        if bufsize == 0:
            # read everything on the socket
            while True:
                avail = self.available()
                if avail:
                    if self._sock_type == SOCK_STREAM:
                        self._buffer += _the_interface.socket_read(self.socknum, avail)[
                            1
                        ]
                    elif self._sock_type == SOCK_DGRAM:
                        self._buffer += _the_interface.read_udp(self.socknum, avail)[1]
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
                if self._sock_type == SOCK_STREAM:
                    recv = _the_interface.socket_read(
                        self.socknum, min(to_read, avail)
                    )[1]
                elif self._sock_type == SOCK_DGRAM:
                    recv = _the_interface.read_udp(self.socknum, min(to_read, avail))[1]
                recv = bytes(recv)
                received.append(recv)
                to_read -= len(recv)
                gc.collect()
            if self._timeout > 0 and time.monotonic() - stamp > self._timeout:
                break
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

    def recvfrom(self, bufsize=0, flags=0):
        """Reads some bytes from the connected remote address.
        :param int bufsize: Maximum number of bytes to receive.
        :param int flags: ignored, present for compatibility.
        :returns: a tuple (bytes, address) where address is a tuple (ip, port)
        """
        return (
            self.recv(bufsize),
            (
                _the_interface.remote_ip(self.socknum),
                _the_interface.remote_port(self.socknum),
            ),
        )

    def recv_into(self, buf, nbytes=0, flags=0):
        """Reads some bytes from the connected remote address info the provided buffer.
        :param bytearray buf: Data buffer
        :param nbytes: Maximum number of bytes to receive
        :param int flags: ignored, present for compatibility.
        :returns: the number of bytes received
        """
        if nbytes == 0:
            nbytes = len(buf)
        ret = self.recv(nbytes)
        nbytes = len(ret)
        buf[:nbytes] = ret
        return nbytes

    def recvfrom_into(self, buf, nbytes=0, flags=0):
        """Reads some bytes from the connected remote address info the provided buffer.
        :param bytearray buf: Data buffer
        :param nbytes: Maximum number of bytes to receive
        :param int flags: ignored, present for compatibility.
        :returns a tuple (nbytes, address) where address is a tuple (ip, port)
        """
        return (
            self.recv_into(buf, nbytes),
            (
                _the_interface.remote_ip(self.socknum),
                _the_interface.remote_port(self.socknum),
            ),
        )

    def readline(self):
        """Attempt to return as many bytes as we can up to \
        but not including '\r\n'.

        """
        stamp = time.monotonic()
        while b"\r\n" not in self._buffer:
            avail = self.available()
            if avail:
                if self._sock_type == SOCK_STREAM:
                    self._buffer += _the_interface.socket_read(self.socknum, avail)[1]
                elif self._sock_type == SOCK_DGRAM:
                    self._buffer += _the_interface.read_udp(self.socknum, avail)[1]
            if (
                not avail
                and self._timeout > 0
                and time.monotonic() - stamp > self._timeout
            ):
                self.close()
                raise RuntimeError("Didn't receive response, failing out...")
        firstline, self._buffer = self._buffer.split(b"\r\n", 1)
        gc.collect()
        return firstline

    def disconnect(self):
        """Disconnects a TCP socket."""
        assert self._sock_type == SOCK_STREAM, "Socket must be a TCP socket."
        _the_interface.socket_disconnect(self.socknum)

    def close(self):
        """Closes the socket."""
        _the_interface.socket_close(self.socknum)

    def available(self):
        """Returns how many bytes of data are available to be read from the socket."""
        return _the_interface.socket_available(self.socknum, self._sock_type)

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
