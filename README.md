# ocr-consumed-energy-logger
Raspberry Pi project for logging OCR-ed readings from consumed energy meter.

# About
This program is used to recognize readings from energy meter like this:

![readings](./samples/readings-1.jpg)

and log them to Google Sheets for further analysis.

# Requirements

## Development setup

In order to develop the algorithm and experiment with OpenCV I used [Jupyter notebook](./ocr-notebook.ipynb).
To run it and other dev tools we need Python 3 and [tesseract](https://tesseract-ocr.github.io):

```shell
$ brew install tesseract
```

It is advisable to install [virtualenv](https://virtualenv.pypa.io) and create new isolated environment in the project difrectory:

```shell
$ virtualenv venv
$ source venv/bin/activate
```

Then run pip to install development dependencies:

```shell
$ pip install -r requirements.txt
```

After that one could run included Jupyter notebook in an environment of choice, for instace in [VS Code](https://code.visualstudio.com/docs/datascience/jupyter-notebooks).

## Raspberry Pi setup

To run the code on Raspbian we need to install the following dependencies (see https://singleboardblog.com/install-python-opencv-on-raspberry-pi/):

```shell
$ apt-get install
```

Check [this guide](https://projects.raspberrypi.org/en/projects/getting-started-with-picamera) for installing camera in Raspberry Pi.

# Credits
Tesseract traineddata for recognizing Seven Segment Display was taken from [this great repository](https://github.com/Shreeshrii/tessdata_ssd)
