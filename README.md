# PICO rgb HID keypad

### All files are in the repository because I know they work. I have also reference the authors so that updates may be located should this repository fall behind

# Steps to install

1. Flash your PICO with the Circuit Python uf2 file. [ORIGINAL FILE][UF2]
1. Download the Circuit Python bundle files. [adafruit-circuitpython-bundle-py-20210214.zip][BUNDLE_FILES]
  1. Create a `lib/` directory on your PICO
  1. Copy all `lib/adafruit_hid` folder to `CIRCUITPY/lib/`
  1. Copy the `lib/adafruit_dotstar.py` file to `CIRCUITPY/lib/adafruit_dotstar.py`
1. In [Thonny][THONNY], create and new file like [`code.py`][CODEPY] and save

![Structure](images/directory.png)



[UF2]: https://circuitpython.org/board/raspberry_pi_pico/
[BUNDLE_FILES]: https://github.com/adafruit/Adafruit_CircuitPython_Bundle/releases
[CODEPY]: https://gist.github.com/wildestpixel/9a69ef420657af3a4aafba2804d1f8e8
[THONNY]: https://thonny.org/
