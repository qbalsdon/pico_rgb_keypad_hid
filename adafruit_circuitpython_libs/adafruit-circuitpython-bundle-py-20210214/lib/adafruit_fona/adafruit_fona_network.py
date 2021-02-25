# SPDX-FileCopyrightText: 2020 Brent Rubell for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_fona_network`
=================================================================================

Interface for connecting to and interacting with GSM and CDMA cellular networks.

* Author(s): Brent Rubell

"""

# Network types
NET_GSM = 0x01
NET_CDMA = 0x02


class CELLULAR:
    """Interface for connecting to and interacting with GSM and CDMA cellular networks."""

    def __init__(self, fona, apn):
        """Initializes interface with cellular network.
        :param adafruit_fona fona: The Adafruit FONA module we are using.
        :param tuple apn: Tuple containing APN name, (optional) APN username,
                            and APN password.

        """
        self._iface = fona
        self._apn = apn
        self._network_connected = False
        self._network_type = NET_CDMA

        if not self._iface.version == 0x4 or self._iface.version == 0x5:
            self._network_type = NET_GSM
            self._iface.gps = True

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        self.disconnect()

    @property
    def imei(self):
        """Returns the modem's IEMI number, as a string."""
        return self._iface.iemi

    @property
    def iccid(self):
        """Returns the SIM card's ICCID, as a string."""
        return self._iface.iccid

    @property
    def is_attached(self):
        """Returns if the modem is attached to the network."""
        if self._network_type == NET_GSM:
            if self._iface.gps == 3 and self._iface.network_status == 1:
                return True
        else:  # Attach CDMA network
            if self._iface.ue_system_info == 1 and self._iface.network_status == 1:
                return True
        return False

    @property
    def is_connected(self):
        """Returns if attached to network and an IP Addresss was obtained."""
        if not self._network_connected:
            return False
        return True

    def connect(self):
        """Connect to cellular network."""
        if self._iface.set_gprs(self._apn, True):
            self._network_connected = True
        else:
            # reset context for next connection attempt
            self._iface.set_gprs(self._apn, False)

    def disconnect(self):
        """Disconnect from cellular network."""
        self._iface.set_gprs(self._apn, False)
        self._network_connected = False
