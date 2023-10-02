# ocr-consumed-energy-logger
Raspberry Pi project for logging OCR-ed readings from consumed energy meter.

# About
This program is used to recognize readings from energy meter like this:

![Meter](./img/readings-1.jpg)

and log them to Google Sheets for further analysis.

# Requirements

## Development setup

In order to develop the algorithm and experiment with OpenCV I used [Jupyter notebook](./ocr-notebook.ipynb).
To run it and other dev tools we need Python 3 and [tesseract](https://tesseract-ocr.github.io). For development I use Mac OS, so the following steps will assume it:

```console
user@macos$ brew install tesseract
```

It is advisable to install [virtualenv](https://virtualenv.pypa.io) and create new isolated environment in the project difrectory:

```console
user@macos$ virtualenv venv
user@macos$ source venv/bin/activate
```

Then run pip to install development dependencies:

```console
user@macos$ pip install -r requirements.txt
```

After that one could run included Jupyter notebook in an environment of choice, for instance in [VS Code](https://code.visualstudio.com/docs/datascience/jupyter-notebooks).



# Hardware

In terms of the hardware I used Raspberry Pi Zero W with [ZeroCam module](https://www.kiwi-electronics.com/en/camera-module-for-raspberry-pi-zero-3882) and it looks pretty much like this:

| ![RPi front](./img/rpi-1.jpg) | ![RPi back](./img/rpi-2.jpg) |
| --- | --- |

For highlighting the scene I used 2 [clear LEDs](https://www.kiwi-electronics.com/en/3mm-led-clear-white-10-pack-3099) working at 3.1V and drawing 20mA. To turn them on I'll use 3.3V signal on GPIO pins. Since working voltage of the LED is lower we need to drop 3.3V down to 3.1V using dropping resitor. In order to calculate resistor parameters I used [this calculator](https://www.pcboard.ca/led-dropping-resistor-calculator) which gave me [10 ohm](https://www.kiwi-electronics.com/en/electronics-parts-components-113/passive-components-211/resistor-10-ohm-1-4-watt-5-10-pack-643).

## Raspberry Pi setup

To run the energy logger code on Raspbian we need to install a number of dependencies. First, we need OpenCV dependencies and tesseract OCR engine. Note, that all the commands prefixed with `user@raspberrypi` will need to be executed on Raspberry Pi:

```console
user@raspberrypi$ sudo apt-get update 
user@raspberrypi$ sudo apt-get install python3-opencv tesseract-ocr
```

Then create `energy-logger` user for running the app and add it to `gpio` and `video` groups:

```console
user@raspberrypi$ sudo adduser energy-logger
user@raspberrypi$ sudo adduser energy-logger gpio
user@raspberrypi$ sudo adduser energy-logger video
```

Now, copy the `app` directory to the home directory of the `energy-logger` user. On the host computer run:

```console
user@macos$ scp -r ./app energy-logger@raspberrypi.local:~
energy-logger@raspberrypi.local's password:
```

Type `energy-logger`'s password when asked. After command completes the `app` directory should appear under `energy-logger` user home directory. Note that it's rather bad security practice to allow ssh password authentication, but for the sake of simplicity I used Raspbian defaults, read [here](https://www.cyberciti.biz/faq/how-to-disable-ssh-password-login-on-linux/) to learn how to disable it.

And then we can install energy logger Python dependencies (on the Raspberry Pi):

```console
user@raspberrypi$ sudo su energy-logger
energy-logger@raspberrypi$ cd ~/app
energy-logger@raspberrypi$ pip install -r requirements.txt
```

Check [this guide](https://projects.raspberrypi.org/en/projects/getting-started-with-picamera) for installing camera in Raspberry Pi.

# Credits
Tesseract traineddata for recognizing Seven Segment Display was taken from [this great repository](https://github.com/Shreeshrii/tessdata_ssd)
