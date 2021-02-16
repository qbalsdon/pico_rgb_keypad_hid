# PICO rgb HID keypad

### All files are in the repository because I know they work. I have also reference the authors so that updates may be located should this repository fall behind

# Steps for basic install

1. Flash your PICO with the Circuit Python uf2 file. [ORIGINAL FILE][UF2]
1. Download the Circuit Python bundle files. [adafruit-circuitpython-bundle-py-20210214.zip][BUNDLE_FILES]
  1. Create a `lib/` directory on your PICO
  1. Copy all `lib/adafruit_hid` folder to `CIRCUITPY/lib/`
  1. Copy the `lib/adafruit_dotstar.py` file to `CIRCUITPY/lib/adafruit_dotstar.py`
1. In [Thonny][THONNY], create and new file like [`code.py`][CODEPY] and save it to the PICO directory (`CIRCUITPY`)

![Structure](images/directory.png)

# Steps for installing my repo

1. Do a basic installation
1. Copy all my python scripts, including `code.py` to the `CIRCUITPY/` directory

# Case

Download the files for 3D Printing a case [from thingiverse][THINGIVERSE_CASE]

[UF2]: https://circuitpython.org/board/raspberry_pi_pico/
[BUNDLE_FILES]: https://github.com/adafruit/Adafruit_CircuitPython_Bundle/releases
[CODEPY]: https://gist.github.com/wildestpixel/6b684b8bc886392f7c4c57015fab3d97
[THONNY]: https://thonny.org/
[THINGIVERSE_CASE]: https://www.thingiverse.com/thing:4761251
