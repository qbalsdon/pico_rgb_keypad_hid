# SPDX-FileCopyrightText: 2017 Tony DiCola for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_tlc59711`
====================================================

CircuitPython module for the TLC59711 16-bit 12 channel LED PWM driver.  See
examples/simpletest.py for a demo of the usage.

* Author(s): Tony DiCola

Implementation Notes
--------------------

**Hardware:**

* Adafruit `12-Channel 16-bit PWM LED Driver - SPI Interface - TLC59711
  <https://www.adafruit.com/product/1455>`_ (Product ID: 1455)

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the ESP8622 and M0-based boards:
  https://github.com/adafruit/circuitpython/releases
"""
__version__ = "1.2.5"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_TLC59711.git"


# Globally disable invalid-name check as this chip by design has short channel
# and register names.  It is confusing to rename these from what the datasheet
# refers to them as.
# pylint: disable=invalid-name

# Globally disable too many instance attributes check.  Again this is a case
# where pylint doesn't have the right context to make this call.  The chip by
# design has many channels which must be exposed.
# pylint: disable=too-many-instance-attributes

# Globally disable protected access.  Once again pylint can't figure out the
# context for using internal decorate classes below.  In these cases protectected
# access is by design for the internal class.
# pylint: disable=protected-access

# Yet another pylint issue, it fails to recognize a decorator class by
# definition has no public methods.  Disable the check.
# pylint: disable=too-few-public-methods


def _shift_in(target_byte, val):
    # Shift in a new bit value to the provided target byte.  The byte will be
    # shift one position left and a new bit inserted that's a 1 if val is true,
    # of a 0 if false.
    target_byte <<= 1
    if val:
        target_byte |= 0x01
    return target_byte


class TLC59711:
    """TLC59711 16-bit 12 channel LED PWM driver.  This chip is designed to
    drive 4 RGB LEDs with 16-bit PWM control of each LED.  The class has an
    interface much like that of NeoPixels with attribute access to the 4
    RGB channels (note they are 16-bit values).  Or you can access each
    independent channel by name (r0, g0, b0, r1, b1, etc.) as properties for
    fine-grained control.

    :param ~busio.SPI spi: An instance of the SPI bus connected to the chip.  The clock and
        MOSI/outout must be set, the MISO/input is unused.
    :param bool auto_show: This is a boolean that defaults to True and indicates any
        change to a channel value will instantly be written to the chip. You might wish to
        set this to false if you desire to perform your own atomic operations of channel
        values. In that case call the show function after making updates to channel state.
    """

    class _GS_Value:
        # Internal decorator to simplify exposing each 16-bit LED PWM channel.
        # These will get/set the appropriate bytes in the shift register with
        # the specified values.

        def __init__(self, byte_offset):
            # Keep track of the byte within the shift register where this
            # 16-bit value starts.  Luckily these are all aligned on byte
            # boundaries.  Note the byte order is big endian (MSB first).
            self._byte_offset = byte_offset

        def __get__(self, obj, obj_type):
            # Grab the 16-bit value at the offset for this channel.
            return (obj._shift_reg[self._byte_offset] << 8) | obj._shift_reg[
                self._byte_offset + 1
            ]

        def __set__(self, obj, val):
            # Set the 16-bit value at the offset for this channel.
            assert 0 <= val <= 65535
            obj._shift_reg[self._byte_offset] = (val >> 8) & 0xFF
            obj._shift_reg[self._byte_offset + 1] = val & 0xFF
            # Write out the new values if auto_show is enabled.
            if obj.auto_show:
                obj._write()

    # Define explicit GS channels (each LED PWM channel) for users to control.
    # See also the __len__ and iterable dunder methods that provide a
    # neopixel-like interface to the GS channel values too.  Each has a
    # trade-off in usage so users can decide how they choose to use the class
    # (must change all 3 values at a time with neopixel-like interface vs.
    # direct single channel control with these properties below).
    b3 = _GS_Value(4)
    g3 = _GS_Value(6)
    r3 = _GS_Value(8)

    b2 = _GS_Value(10)
    g2 = _GS_Value(12)
    r2 = _GS_Value(14)

    b1 = _GS_Value(16)
    g1 = _GS_Value(18)
    r1 = _GS_Value(20)

    b0 = _GS_Value(22)
    g0 = _GS_Value(24)
    r0 = _GS_Value(26)

    def __init__(self, spi, *, auto_show=True):
        self._spi = spi
        # This device is just a big 28 byte long shift register without any
        # fancy update protocol.  Blast out all the bits to update, that's it!
        self._shift_reg = bytearray(28)
        # Keep track of automatically writing out the state of the PWM channels
        # on any change (auto_show = True).  If set to false the user must
        # explicitly call the show method to write out the PWM state to the
        # chip--this is useful for performing atomic updates to LEDs (i.e.
        # changing all the R, G, B channels at once).
        self.auto_show = auto_show
        # Initialize the brightness channel values to max (these are 7-bit
        # values).
        self._bcr = 127
        self._bcg = 127
        self._bcb = 127
        # Initialize external user-facing state for the function control
        # bits of the chip.  These aren't commonly used but available and
        # match the nomenclature from the datasheet.  Note they won't honor
        # the auto_show property and instead you must manually call show
        # after changing them (reduces the need to make frivolous
        # memory-hogging properties).
        # Set OUTTMG, TMGRST, and DSPRPT to on like the Arduino library.
        self.outtmg = True
        self.extgclk = False
        self.tmgrst = True
        self.dsprpt = True
        self.blank = False

    def _write(self):
        # Write out the current state to the shift register.
        try:
            # Lock the SPI bus and configure it for the shift register.
            while not self._spi.try_lock():
                pass
            self._spi.configure(baudrate=self._spi.frequency, polarity=0, phase=0)
            # Update the preamble of chip state in the first 4 bytes (32-bits)
            # with the write command, function control bits, and brightness
            # control register values.
            self._shift_reg[0] = 0x25  # 0x25 in top 6 bits initiates write.
            # Lower two bits control OUTTMG and EXTGCLK bits, set them
            # as appropriate.
            self._shift_reg[0] = _shift_in(self._shift_reg[0], self.outtmg)
            self._shift_reg[0] = _shift_in(self._shift_reg[0], self.extgclk)
            # Next byte contains remaining function control state and start of
            # brightness control bits.
            self._shift_reg[1] = 0x00
            self._shift_reg[1] = _shift_in(self._shift_reg[1], self.tmgrst)
            self._shift_reg[1] = _shift_in(self._shift_reg[1], self.dsprpt)
            self._shift_reg[1] = _shift_in(self._shift_reg[1], self.blank)
            # Top 5 bits from BC blue channel.
            self._shift_reg[1] <<= 5
            self._shift_reg[1] |= (self._bcb >> 2) & 0b11111
            # Next byte contains lower 2 bits from BC blue channel and upper 6
            # from BC green channel.
            self._shift_reg[2] = (self._bcb) & 0b11
            self._shift_reg[2] <<= 6
            self._shift_reg[2] |= (self._bcg >> 1) & 0b111111
            # Final byte contains lower 1 bit from BC green and 7 bits from BC
            # red channel.
            self._shift_reg[3] = self._bcg & 0b1
            self._shift_reg[3] <<= 7
            self._shift_reg[3] |= self._bcr & 0b1111111
            # The remaining bytes in the shift register are the channel PWM
            # values that have already been set by the user.  Now write out the
            # the entire set of bytes.  Note there is no latch or other
            # explicit line to tell the chip when finished, it expects 28 bytes.
            self._spi.write(self._shift_reg)
        finally:
            # Ensure the SPI bus is unlocked.
            self._spi.unlock()

    def show(self):
        """Write out the current LED PWM state to the chip.  This is only necessary if
        auto_show was set to false in the initializer.
        """
        self._write()

    # Define properties for global brightness control channels.
    @property
    def red_brightness(self):
        """The red brightness for all channels (i.e. R0, R1, R2, and R3).  This is a 7-bit
        value from 0-127.
        """
        return self._bcr

    @red_brightness.setter
    def red_brightness(self, val):
        assert 0 <= val <= 127
        self._bcr = val
        if self.auto_show:
            self._write()

    @property
    def green_brightness(self):
        """The green brightness for all channels (i.e. G0, G1, G2, and G3).  This is a
        7-bit value from 0-127.
        """
        return self._bcg

    @green_brightness.setter
    def green_brightness(self, val):
        assert 0 <= val <= 127
        self._bcg = val
        if self.auto_show:
            self._write()

    @property
    def blue_brightness(self):
        """The blue brightness for all channels (i.e. B0, B1, B2, and B3).  This is a 7-bit
        value from 0-127.
        """
        return self._bcb

    @blue_brightness.setter
    def blue_brightness(self, val):
        assert 0 <= val <= 127
        self._bcb = val
        if self.auto_show:
            self._write()

    # Define index and length properties to set and get each channel as
    # atomic RGB tuples.  This provides a similar feel as using neopixels.
    def __len__(self):
        """Retrieve the total number of LED channels available."""
        return 4  # Always 4 RGB channels on the chip.

    def __getitem__(self, key):
        # pylint: disable=no-else-return
        # Disable should be removed when refactor can be tested
        """Retrieve the R, G, B values for the provided channel as a
        3-tuple. Each value is a 16-bit number from 0-65535.
        """
        if key == 0:
            return (self.r0, self.g0, self.b0)
        elif key == 1:
            return (self.r1, self.g1, self.b1)
        elif key == 2:
            return (self.r2, self.g2, self.b2)
        elif key == 3:
            return (self.r3, self.g3, self.b3)
        else:
            raise IndexError

    def __setitem__(self, key, val):
        """Set the R, G, B values for the provided channel.  Specify a
        3-tuple of R, G, B values that are each 16-bit numbers (0-65535).
        """
        assert 0 <= key <= 3  # Do this check here instead of later to
        # prevent accidentally keeping auto_show
        # turned off when a bad key is provided.
        assert len(val) == 3
        assert 0 <= val[0] <= 65535
        assert 0 <= val[1] <= 65535
        assert 0 <= val[2] <= 65535
        # Temporarily halt auto write to perform an atomic update of all
        # the channel values.
        old_auto_show = self.auto_show
        self.auto_show = False
        # Update appropriate channel values.
        if key == 0:
            self.r0, self.g0, self.b0 = val
        elif key == 1:
            self.r1, self.g1, self.b1 = val
        elif key == 2:
            self.r2, self.g2, self.b2 = val
        elif key == 3:
            self.r3, self.g3, self.b3 = val
        # Restore auto_show state.
        self.auto_show = old_auto_show
        # Write out new values if in auto_show state.
        if self.auto_show:
            self._write()
