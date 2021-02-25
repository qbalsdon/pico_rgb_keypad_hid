# SPDX-FileCopyrightText: Copyright (c) 2020 Dan Halbert for Adafruit Industries
#
# SPDX-License-Identifier: MIT
"""
`adafruit_airlift.esp32`
================================================================================

ESP32 Adapter Support

* Author(s): Dan Halbert
"""

import time

import board
import busio
from digitalio import DigitalInOut


class ESP32:
    """Class to manage ESP32 running NINA firmware for WiFi or Bluetooth."""

    NOT_IN_USE = 0
    """Not currently being used."""
    BOOTLOADER = 1
    """Put ESP32 into bootloader mode."""
    BLUETOOTH = 2
    """HCI Bluetooth mode."""
    WIFI = 3
    """WiFi mode."""
    _MODES = (NOT_IN_USE, BOOTLOADER, BLUETOOTH, WIFI)

    # pylint: disable=invalid-name
    def __init__(
        self,
        *,
        reset=None,
        reset_high=False,
        gpio0=None,
        busy=None,
        chip_select=None,
        tx=None,
        rx=None,
        spi=None
    ):

        """Create an ESP32 instance, passing the objects needed to reset and communicate
        with the adapter.

        :param reset ~microcontroller.Pin: ESP32 RESET pin.
           If `None`, use ``board.ESP_RESET``.
        :param reset_high bool: True if `reset` is brought high to reset;
            `False` if brought low.
        :param gpio0 ~microcontroller.Pin: ESP32 GPIO0 pin.
           Used for ESP32 boot selection when reset, and as RTS for UART communication.
           If `None`, use ``board.ESP_GPIO0``.
        :param busy ~microcontroller.Pin: ESP32 BUSY pin (sometimes called READY).
           Used as CTS indicator for UART communication.
           If `None`, use ``board.ESP_BUSY``.
        :param chip_select ~microcontroller.Pin: ESP32 CS (chip select) pin.
            Also used for ESP32 mode selection when reset.
            If `None`, use ``board.ESP_CS``.
        :param tx ~microcontroller.Pin: ESP32 TX pin for Bluetooth UART communication.
           If `None`, use ``board.ESP_TX`` when in Bluetooth mode.
        :param rx ~microcontroller.Pin: ESP32 RX pin for Bluetooth UART communication.
           If `None`, use ``board.ESP_RX`` when in Bluetooth mode.
        :param spi busio.SPI: Used for communication with the ESP32.
          If not supplied, ``board.SPI()`` is used when in WiFi mode.
        """
        self._mode = ESP32.NOT_IN_USE

        # We can't use board.ESP_RESET, etc. as defaults, because they may not exist.
        self._reset = DigitalInOut(reset or board.ESP_RESET)
        # Turn off ESP32 by holding reset line
        self._reset.switch_to_output(reset_high)
        self._reset_high = reset_high

        # These will be set to input or input as necessary.
        self._gpio0_rts = DigitalInOut(gpio0 or board.ESP_GPIO0)
        self._busy_cts = DigitalInOut(busy or board.ESP_BUSY)
        self._chip_select = DigitalInOut(chip_select or board.ESP_CS)

        # Used for Bluetooth mode.
        self._tx = tx
        self._rx = rx
        self._uart = None
        self._bleio_adapter = None

        # Used for WiFi mode.
        self._spi = spi

    def reset(self, mode, debug=False):
        """Do hard reset of the ESP32.

        :param mode: One of `ESP32.NOT_IN_USE`, `ESP32.BOOTLOADER`, `ESP32.BLUETOOTH`, `ESP32.WIFI`.
        """
        if mode not in ESP32._MODES:
            raise ValueError("Invalid mode")

        # GPIO0 high means boot from SPI flash.
        # Low means go into bootloader mode.
        self._gpio0_rts.switch_to_output(mode != ESP32.BOOTLOADER)

        if mode == ESP32.NOT_IN_USE:
            # Turn of ESP32 by holding reset line.
            self._reset.switch_to_output(self._reset_high)
            self._mode = mode
            return

        if mode == ESP32.BLUETOOTH:
            self._chip_select.switch_to_output(False)
        elif mode == ESP32.WIFI:
            self._chip_select.switch_to_output(True)

        # Initial mode. Changed if reset is successful.
        self._mode = ESP32.NOT_IN_USE

        # Reset by toggling reset pin for 100ms
        self._reset.switch_to_output(self._reset_high)
        time.sleep(0.1)
        self._reset.value = not self._reset_high

        #  Wait 1 second for startup.
        time.sleep(1.0)

        if mode == ESP32.BOOTLOADER:
            # No startup message expected.
            return

        startup_message = b""
        while self._uart.in_waiting:  # pylint: disable=no-member
            more = self._uart.read()
            if more:
                startup_message += more

        if not startup_message:
            raise RuntimeError("ESP32 did not respond with a startup message")
        if debug:
            try:
                print(startup_message.decode("utf-8"))
            except UnicodeError:
                raise RuntimeError("Garbled ESP32 startup message") from UnicodeError

        # Everything's fine. Remember mode.
        self._mode = mode

    # pylint: disable=invalid-name
    def start_bluetooth(self, debug=False):
        """Set up the ESP32 in HCI Bluetooth mode, if it is not already doing something else.

        :param debug bool: Print out some debugging information.
        :return: A `_bleio.Adapter`, to be passed to ``_bleio.set_adapter()``.
        """
        # Will fail with ImportError if _bleio is not on the board.
        # That exception is probably good enough.
        # pylint: disable=import-outside-toplevel
        import _bleio

        if self._mode == ESP32.BLUETOOTH:
            # Already started.
            return _bleio.adapter

        if self._mode == ESP32.WIFI:
            raise RuntimeError("ESP32 is in WiFi mode; use stop_wifi() first")

        # Choose Bluetooth mode.
        self._chip_select.switch_to_output(False)

        self._uart = busio.UART(
            self._tx or board.ESP_TX,
            self._rx or board.ESP_RX,
            baudrate=115200,
            timeout=0,
            receiver_buffer_size=512,
        )

        # Reset into Bluetooth mode.
        self.reset(ESP32.BLUETOOTH, debug=debug)

        self._busy_cts.switch_to_input()
        self._gpio0_rts.switch_to_output()
        # pylint: disable=no-member
        # pylint: disable=unexpected-keyword-arg
        self._bleio_adapter = _bleio.Adapter(
            uart=self._uart, rts=self._gpio0_rts, cts=self._busy_cts
        )
        self._bleio_adapter.enabled = True
        return self._bleio_adapter

    def stop_bluetooth(self):
        """Stop Bluetooth on the ESP32. Deinitialize the ~busio.UART used for communication"""
        if self._mode != ESP32.BLUETOOTH:
            return
        self._bleio_adapter.enabled = False
        self.reset(ESP32.NOT_IN_USE)
        self._uart.deinit()
        self._uart = None

    def start_wifi(self, debug=False):
        """Start WiFi on the ESP32.

        :return: the ``busio.SPI`` object that will be used to communicate with the ESP32.
        :rtype: busio.SPI
        """
        if self._mode == ESP32.WIFI:
            # Already started.
            return self._spi

        if self._mode == ESP32.BLUETOOTH:
            raise RuntimeError("ESP32 is in Bluetooth mode; use stop_bluetooth() first")

        self.reset(ESP32.WIFI, debug=debug)
        if self._spi is None:
            self._spi = board.SPI()
        return self._spi

    def stop_wifi(self):
        """Stop WiFi on the ESP32.
        The `busio.SPI` object used is not deinitialized, since it may be in use for other devices.
        """
        if self._mode != ESP32.WIFI:
            return
        self.reset(ESP32.NOT_IN_USE)
