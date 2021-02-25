# SPDX-FileCopyrightText: 2017 ladyada for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_avrprog`
====================================================

Program your favorite AVR chips directly from CircuitPython with this
handy helper class that will let you make stand-alone programmers right
from your REPL

* Author(s): ladyada

Implementation Notes
--------------------

**Hardware:**

* See Learn Guide for supported hardware: `Stand-alone programming AVRs using CircuitPython
  <https://learn.adafruit.com/stand-alone-programming-avrs-using-circuitpython/overview>`_

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the ESP8622 and M0-based boards:
  https://github.com/adafruit/circuitpython/releases

"""

# imports

__version__ = "1.3.5"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_AVRprog.git"

from digitalio import Direction, DigitalInOut

_SLOW_CLOCK = 100000
_FAST_CLOCK = 1000000


class AVRprog:
    """
    Helper class used to program AVR chips from CircuitPython.
    """

    class Boards:
        """
        Some well known board definitions.
        """

        # pylint: disable=too-few-public-methods
        ATtiny13a = {
            "name": "ATtiny13a",
            "sig": [0x1E, 0x90, 0x07],
            "flash_size": 1024,
            "page_size": 32,
            "fuse_mask": (0xFF, 0xFF, 0x00, 0x03),
            "clock_speed": 100000,
        }
        ATtiny85 = {
            "name": "ATtiny85",
            "sig": [0x1E, 0x93, 0x0B],
            "flash_size": 8192,
            "page_size": 64,
            "fuse_mask": (0xFF, 0xFF, 0x07, 0x3F),
        }
        ATmega328p = {
            "name": "ATmega328p",
            "sig": [0x1E, 0x95, 0x0F],
            "flash_size": 32768,
            "page_size": 128,
            "fuse_mask": (0xFF, 0xFF, 0x07, 0x3F),
        }
        ATmega2560 = {
            "name": "ATmega2560",
            "sig": [0x1E, 0x98, 0x01],
            "flash_size": 262144,
            "page_size": 256,
            "fuse_mask": (0xFF, 0xFF, 0x07, 0x3F),
        }

    _spi = None
    _rst = None

    def init(self, spi_bus, rst_pin):
        """
        Initialize the programmer with an SPI port that will be used to
        communicate with the chip. Make sure your SPI supports 'write_readinto'
        Also pass in a reset pin that will be used to get into programming mode
        """
        self._spi = spi_bus
        self._rst = DigitalInOut(rst_pin)
        self._rst.direction = Direction.OUTPUT
        self._rst.value = True

    def verify_sig(self, chip, verbose=False):
        """
        Verify that the chip is connected properly, responds to commands,
        and has the correct signature. Returns True/False based on success
        """
        self.begin(clock=_SLOW_CLOCK)
        sig = self.read_signature()
        self.end()
        if verbose:
            print("Found signature: %s" % [hex(i) for i in sig])
        if sig != chip["sig"]:
            return False
        return True

    def program_file(self, chip, file_name, verbose=False, verify=True):
        """
        Perform a chip erase and program from a file that
        contains Intel HEX data. Returns true on verify-success, False on
        verify-failure. If 'verify' is False, return will always be True
        """
        if not self.verify_sig(chip):
            raise RuntimeError("Signature read failure")

        if verbose:
            print("Erasing chip....")
        self.erase_chip()

        clock_speed = getattr(chip, "clock_speed", _FAST_CLOCK)
        self.begin(clock=clock_speed)

        # create a file state dictionary
        file_state = {"line": 0, "ext_addr": 0, "eof": False}
        file_state["f"] = open(file_name, "r")

        page_size = chip["page_size"]

        for page_addr in range(0, chip["flash_size"], page_size):
            if verbose:
                print("Programming page $%04X..." % page_addr, end="")
            page_buffer = bytearray(page_size)
            for b in range(page_size):
                page_buffer[b] = 0xFF  # make an empty page

            read_hex_page(file_state, page_addr, page_size, page_buffer)

            if all([v == 0xFF for v in page_buffer]):
                if verbose:
                    print("skipping")
                continue

            # print("From HEX file: ", page_buffer)
            self._flash_page(bytearray(page_buffer), page_addr, page_size)

            if not verify:
                if verbose:
                    print("done!")
                continue

            if verbose:
                print("Verifying page @ $%04X" % page_addr)
            read_buffer = bytearray(page_size)
            self.read(page_addr, read_buffer)
            # print("From memory: ", read_buffer)

            if page_buffer != read_buffer:
                if verbose:
                    # pylint: disable=line-too-long
                    print(
                        "Verify fail at address %04X\nPage should be: %s\nBut contains: %s"
                        % (page_addr, page_buffer, read_buffer)
                    )
                    # pylint: enable=line-too-long
                self.end()
                return False

            if file_state["eof"]:
                break  # we're done, bail!

        file_state["f"].close()
        self.end()
        return True

    def verify_file(self, chip, file_name, verbose=False):
        """
        Perform a chip full-flash verification from a file that
        contains Intel HEX data. Returns True/False on success/fail.
        """
        if not self.verify_sig(chip):
            raise RuntimeError("Signature read failure")

        # create a file state dictionary
        file_state = {"line": 0, "ext_addr": 0, "eof": False}
        file_state["f"] = open(file_name, "r")

        page_size = chip["page_size"]
        clock_speed = getattr(chip, "clock_speed", _FAST_CLOCK)
        self.begin(clock=clock_speed)
        for page_addr in range(0x0, chip["flash_size"], page_size):
            page_buffer = bytearray(page_size)
            for b in range(page_size):
                page_buffer[b] = 0xFF  # make an empty page

            read_hex_page(file_state, page_addr, page_size, page_buffer)

            if verbose:
                print("Verifying page @ $%04X" % page_addr)
            read_buffer = bytearray(page_size)
            self.read(page_addr, read_buffer)
            # print("From memory: ", read_buffer)
            # print("From file  : ", page_buffer)

            if page_buffer != read_buffer:
                if verbose:
                    # pylint: disable=line-too-long
                    print(
                        "Verify fail at address %04X\nPage should be: %s\nBut contains: %s"
                        % (page_addr, page_buffer, read_buffer)
                    )
                    # pylint: enable=line-too-long
                self.end()
                return False

            if file_state["eof"]:
                break  # we're done, bail!

        file_state["f"].close()
        self.end()
        return True

    def read_fuses(self, chip):
        """
        Read the 4 fuses and return them in a list (low, high, ext, lock)
        Each fuse is bitwise-&'s with the chip's fuse mask for simplicity
        """
        mask = chip["fuse_mask"]
        self.begin(clock=_SLOW_CLOCK)
        low = self._transaction((0x50, 0, 0, 0))[2] & mask[0]
        high = self._transaction((0x58, 0x08, 0, 0))[2] & mask[1]
        ext = self._transaction((0x50, 0x08, 0, 0))[2] & mask[2]
        lock = self._transaction((0x58, 0, 0, 0))[2] & mask[3]
        self.end()
        return (low, high, ext, lock)

    # pylint: disable=unused-argument,expression-not-assigned
    def write_fuses(self, chip, low=None, high=None, ext=None, lock=None):
        """
        Write any of the 4 fuses. If the kwarg low/high/ext/lock is not
        passed in or is None, that fuse is skipped
        """
        self.begin(clock=_SLOW_CLOCK)
        lock and self._transaction((0xAC, 0xE0, 0, lock))
        low and self._transaction((0xAC, 0xA0, 0, low))
        high and self._transaction((0xAC, 0xA8, 0, high))
        ext and self._transaction((0xAC, 0xA4, 0, ext))
        self.end()

    # pylint: enable=unused-argument,expression-not-assigned

    def verify_fuses(self, chip, low=None, high=None, ext=None, lock=None):
        """
        Verify the 4 fuses. If the kwarg low/high/ext/lock is not
        passed in or is None, that fuse is not checked.
        Each fuse is bitwise-&'s with the chip's fuse mask.
        Returns True on success, False on a fuse verification failure
        """
        fuses = self.read_fuses(chip)
        verify = (low, high, ext, lock)
        for i in range(4):
            # check each fuse if we requested to check it!
            if verify[i] and verify[i] != fuses[i]:
                return False
        return True

    def erase_chip(self):
        """
        Fully erases the chip.
        """
        self.begin(clock=_SLOW_CLOCK)
        self._transaction((0xAC, 0x80, 0, 0))
        self._busy_wait()
        self.end()

    #################### Mid level

    def begin(self, clock=_FAST_CLOCK):
        """
        Begin programming mode: pull reset pin low, initialize SPI, and
        send the initialization command to get the AVR's attention.
        """
        self._rst.value = False
        while self._spi and not self._spi.try_lock():
            pass
        self._spi.configure(baudrate=clock)
        self._transaction((0xAC, 0x53, 0, 0))

    def end(self):
        """
        End programming mode: SPI is released, and reset pin set high.
        """
        self._spi.unlock()
        self._rst.value = True

    def read_signature(self):
        """
        Read and return the signature of the chip as two bytes in an array.
        Requires calling begin() beforehand to put in programming mode.
        """
        # signature is last byte of two transactions:
        sig = []
        for i in range(3):
            sig.append(self._transaction((0x30, 0, i, 0))[2])
        return sig

    def read(self, addr, read_buffer):
        """
        Read a chunk of memory from address 'addr'. The amount read is the
        same as the size of the bytearray 'read_buffer'. Data read is placed
        directly into 'read_buffer'
        Requires calling begin() beforehand to put in programming mode.
        """
        last_addr = 0
        for i in range(len(read_buffer) // 2):
            read_addr = addr // 2 + i  # read 'words' so address is half

            if (last_addr >> 16) != (read_addr >> 16):
                # load extended byte
                # print("Loading extended address",  read_addr >> 16)
                self._transaction((0x4D, 0, read_addr >> 16, 0))
            high = self._transaction((0x28, read_addr >> 8, read_addr, 0))[2]
            low = self._transaction((0x20, read_addr >> 8, read_addr, 0))[2]
            # print("%04X: %02X %02X" % (read_addr*2, low, high))
            read_buffer[i * 2] = low
            read_buffer[i * 2 + 1] = high

            last_addr = read_addr

    #################### Low level
    def _flash_word(self, addr, low, high):
        self._transaction((0x40, addr >> 8, addr, low))
        self._transaction((0x48, addr >> 8, addr, high))

    def _flash_page(self, page_buffer, page_addr, page_size):
        page_addr //= 2  # address is by 'words' not bytes!
        for i in range(page_size / 2):  # page indexed by words, not bytes
            lo_byte, hi_byte = page_buffer[2 * i : 2 * i + 2]
            self._flash_word(i, lo_byte, hi_byte)

        # load extended byte
        self._transaction((0x4D, 0, page_addr >> 16, 0))

        commit_reply = self._transaction((0x4C, page_addr >> 8, page_addr, 0))
        if ((commit_reply[1] << 8) + commit_reply[2]) != (page_addr & 0xFFFF):
            raise RuntimeError("Failed to commit page to flash")
        self._busy_wait()

    def _transaction(self, command):
        reply = bytearray(4)
        command = bytearray([i & 0xFF for i in command])

        self._spi.write_readinto(command, reply)
        # s = [hex(i) for i in command]
        # print("Sending %s reply %s" % ([hex(i) for i in command], [hex(i) for i in reply]))
        if reply[2] != command[1]:
            raise RuntimeError("SPI transaction failed")
        return reply[1:]  # first byte is ignored

    def _busy_wait(self):
        while self._transaction((0xF0, 0, 0, 0))[2] & 0x01:
            pass


def read_hex_page(file_state, page_addr, page_size, page_buffer):
    """
    Helper function that does the Intel Hex parsing. Takes in a dictionary
    that contains the file 'state'. The dictionary should have file_state['f']
    be the file stream object (returned by open), the file_state['line'] which
    tracks the line number of the file for better debug messages. This function
    will update 'line' as it reads lines. It will set 'eof' when the file has
    completed reading. It will also store the 'extended address' state in
    file_state['ext_addr']
    In addition to the file, it takes the desired buffer address start
    (page_addr), size (page_size) and an allocated bytearray.
    This function will try to read the file and fill the page_buffer.
    If the next line has data that is beyond the size of the page_address,
    it will return without changing the buffer, so pre-fill it with 0xFF
    before calling, for sparsely-defined HEX files.
    Returns False if the file has no more data to read. Returns True if
    we've done the best job we can with filling the buffer and the next
    line does not contain any more data we can use.
    """
    while True:  # read until our page_buff is full!
        orig_loc = file_state["f"].tell()  # in case we have to 'back up'
        line = file_state["f"].readline()  # read one line from the HEX file
        file_state["line"] += 1

        if not line:
            file_state["eof"] = True
            return False
        # print(line)
        if line[0] != ":":  # lines must start with ':'
            raise RuntimeError("HEX line %d doesn't start with :" % file_state["line"])

        # Try to parse the line length, address, and record type
        try:
            hex_len = int(line[1:3], 16)
            line_addr = int(line[3:7], 16)
            file_state["line_addr"] = line_addr
            rec_type = int(line[7:9], 16)
        except ValueError as err:
            raise RuntimeError(
                "Could not parse HEX line %d addr" % file_state["line"]
            ) from err

        if file_state["ext_addr"]:
            line_addr += file_state["ext_addr"]
        # print("Hex len: %d, addr %04X, record type %d " % (hex_len, line_addr, rec_type))

        # We should only look for data type records (0x00)
        if rec_type == 1:
            file_state["eof"] = True
            return False  # reached end of file
        if rec_type == 2:
            file_state["ext_addr"] = int(line[9:13], 16) << 4
            # print("Extended addr: %05X" % file_state['ext_addr'])
            continue
        if rec_type == 3:  # sometimes appears, we ignore this
            continue
        if rec_type != 0:  # if not the above or a data record...
            raise RuntimeError(
                "Unsupported record type %d on line %d" % (rec_type, file_state["line"])
            )

        # check if this file file is either after the current page
        # (in which case, we've read all we can for this page and should
        # commence flasing...)
        if line_addr >= (page_addr + page_size):
            # print("Hex is past page address range")
            file_state["f"].seek(orig_loc)  # back up!
            file_state["line"] -= 1
            return True
        # or, this line does not yet reach the current page address, in which
        # case which should just keep reading in hopes we reach the address
        # we're looking for next time!
        if (line_addr + hex_len) <= page_addr:
            # print("Hex is prior to page address range")
            continue

        # parse out all remaining hex bytes including the checksum
        byte_buffer = []
        for i in range(hex_len + 1):
            byte_buffer.append(int(line[9 + i * 2 : 11 + i * 2], 16))

        # check chksum now!
        chksum = (
            hex_len
            + (line_addr >> 8)
            + (line_addr & 0xFF)
            + rec_type
            + sum(byte_buffer)
        )
        # print("checksum: "+hex(chksum))
        if (chksum & 0xFF) != 0:
            raise RuntimeError("HEX Checksum fail")

        # get rid of that checksum byte
        byte_buffer.pop()
        # print([hex(i) for i in byte_buffer])

        # print("line addr $%04X page addr $%04X" % (line_addr, page_addr))
        page_idx = line_addr - page_addr
        line_idx = 0
        while (page_idx < page_size) and (line_idx < hex_len):
            # print("page_idx = %d, line_idx = %d" % (page_idx, line_idx))
            page_buffer[page_idx] = byte_buffer[line_idx]
            line_idx += 1
            page_idx += 1
        if page_idx == page_size:
            return True  # ok we've read a full page, can bail now!

    return False  # we...shouldn't get here?
