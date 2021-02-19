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

A big thank you to [wildestpixel][WILDESTPIXEL] and the [code they made][CODEPY] that formed a basis for this project.

## NOTES:

1. This is in [CircuitPython][CIRCUITPYTHON], please use that as a basis for code questions.
1. Saving files to the `CIRCUITPY` folder will automatically trigger a restart and deploy `code.py`
1. Using the Arduino Serial Monitor to debug has been super useful and was a complete "by chance" discovery
1. This repo is going to be changing (hopefully) rapidly, I'm new to [Insert Brand Name Here]Python and electronics, my main experience in this area has been minor doses of nodejs on a Raspberry Pi.

# My repo

## Introduction

The aim of this is to eventually control a series of different button configurations, I have done some conferences on my [Android developer scripts][TALOS] and thought being able to control various aspects of my "automate-able" life using this little shiny thing will keep me somewhat warm on those long Covid nights.

The goal is to have the code that interfaces with the [Pico Board][PICO] plugged into the [Rainbow Pi Hat][KEYPAD] in the `code.py` file, and then have several classes that implement the specific behaviours that I want as separate "plug-ins." For example, I want to be able to control Microsoft Teams chats easier, these configurations can be found in the `teams.py` file. I have also been musing some DotA2 handiness, and that can be found in the `dota.py` file.

My [Android scripts][TALOS] are fairly specific and relate to the scripts that can be found [in my other repo][TALOS]. They need to be installed in a fairly specific manner and since I'm still new to this I recommend just removing that for now.

If you want to see an example of what the keypad behaviours should do, please use `keypad.py` as the template, and `teams.py` as an example. Currently the 16th button is used to switch through states.

## Installation

1. Do a basic installation
1. Copy all my python scripts, including `code.py` to the `CIRCUITPY/` directory
1. Choose which configurations you want in [line 38][LINE38] of `code.py`, and use the 16th (bottom-right most) button to switch between them

# Case

Download the files for 3D Printing a case [from thingiverse][THINGIVERSE_CASE]

[UF2]: https://circuitpython.org/board/raspberry_pi_pico/
[BUNDLE_FILES]: https://github.com/adafruit/Adafruit_CircuitPython_Bundle/releases
[CODEPY]: https://gist.github.com/wildestpixel/6b684b8bc886392f7c4c57015fab3d97
[THONNY]: https://thonny.org/
[THINGIVERSE_CASE]: https://www.thingiverse.com/thing:4761251
[WILDESTPIXEL]: https://github.com/wildestpixel]
[CIRCUITPYTHON]: https://circuitpython.org/
[TALOS]: https://github.com/qbalsdon/talos
[PICO]: https://www.raspberrypi.org/documentation/pico/getting-started/
[KEYPAD]: https://shop.pimoroni.com/products/pico-rgb-keypad-base
[LINE38]: https://github.com/qbalsdon/pico_rgb_keypad_hid/blob/8f63c366559465032fa30e0789f4867cd539c37c/code.py#L38
