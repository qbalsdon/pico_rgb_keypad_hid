# SPDX-FileCopyrightText: 2017 Scott Shawcroft, written for Adafruit Industries
# SPDX-FileCopyrightText: Copyright (c) 2020 Melissa LeBlanc-Williams for Adafruit Industries
#
# SPDX-License-Identifier: MIT
"""
`adafruit_magtag.network`
================================================================================

Helper library for the Adafruit MagTag.


* Author(s): Melissa LeBlanc-Williams

Implementation Notes
--------------------

**Hardware:**

* `Adafruit MagTag <https://www.adafruit.com/product/4800>`_

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://github.com/adafruit/circuitpython/releases

* Adafruit's PortalBase library: https://github.com/adafruit/Adafruit_CircuitPython_PortalBase

"""

from adafruit_portalbase.network import NetworkBase
from adafruit_magtag.wifi_module import WiFi

__version__ = "1.6.0"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_MagTag.git"


class Network(NetworkBase):
    """Class representing the Adafruit MagTag.

    :param status_neopixel: The pin for the status NeoPixel. Use ``board.NEOPIXEL`` for the on-board
                            NeoPixel. Defaults to ``None``, not the status LED
    :param bool extract_values: If true, single-length fetched values are automatically extracted
                                from lists and tuples. Defaults to ``True``.
    :param debug: Turn on debug print outs. Defaults to False.

    """

    # pylint: disable=too-many-instance-attributes, too-many-locals, too-many-branches, too-many-statements
    def __init__(
        self,
        *,
        status_neopixel=None,
        extract_values=True,
        debug=False,
    ):
        super().__init__(
            WiFi(status_neopixel=status_neopixel),
            extract_values=extract_values,
            debug=debug,
        )

    @property
    def enabled(self):
        """
        Return whether the WiFi is enabled

        """
        return self._wifi.enabled
