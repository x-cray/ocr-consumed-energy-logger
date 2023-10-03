#!/bin/env python

"""
This script takes a picture of an energy meter screen using attached camera module
and recognizes the readings which it subsequently posts to Google Sheets spreadsheet
for further analysis.
"""

import os
from datetime import datetime
import logging
import time
import numpy as np
import cv2
from picamera2 import Picamera2
import RPi.GPIO as io
from reader import meter_reader
from publisher import sheets

LED_1 = 27
LED_2 = 22
SCRIPT_PATH = os.path.realpath(os.path.dirname(__file__))
PICTURES_DIR = os.path.join(SCRIPT_PATH, "pictures")


class ApplicationError(Exception):
    """Application generic exception"""


def flash_indicate_error():
    """Flashes connected LEDs several times to indicate an error"""
    for _ in range(10):
        io.output(LED_1, True)
        time.sleep(0.5)
        io.output(LED_1, False)
        io.output(LED_2, True)
        time.sleep(0.5)
        io.output(LED_2, False)
        time.sleep(0.5)


def flash_on():
    """Turns the flash on"""
    logging.debug("Turning flash on")
    io.output(LED_1, True)
    io.output(LED_2, True)


def flash_off():
    """Turns the flash off"""
    logging.debug("Turning flash off")
    io.output(LED_1, False)
    io.output(LED_2, False)


def take_picture() -> np.ndarray:
    """Takes a picture from connected camera and returns it as a numpy array"""
    logging.info("Capturing a picture from camera")
    camera = Picamera2()
    try:
        config = camera.create_still_configuration({"size": (2592, 1944)})
        camera.align_configuration(config)
        camera.configure(config)
        camera.set_controls({"ExposureTime": 1000000, "ColourGains": (1.5, 1)})
        camera.start()
        flash_on()
        time.sleep(2)
        return camera.capture_array()
    finally:
        camera.stop()
        flash_off()


def save_picture(img, filename):
    """Saves provided image to a file"""
    if not os.path.exists(PICTURES_DIR):
        os.makedirs(PICTURES_DIR)

    image_path = os.path.join(PICTURES_DIR, filename)
    logging.info("Saving image to %s", image_path)
    cv2.imwrite(image_path, cv2.cvtColor(img, cv2.COLOR_BGR2RGB))


def main():
    """Energy logger entry point"""
    picture = None
    try:
        logging.basicConfig(
            format="%(asctime)s [%(levelname)s] %(message)s", level=logging.DEBUG
        )

        sheet_id = os.getenv("SHEET_ID")
        sheet_range = os.getenv("SHEET_RANGE")

        if not sheet_id or not sheet_range:
            raise ApplicationError(
                "Make sure to specify SHEET_ID and SHEET_RANGE environment variables"
            )

        io.setmode(io.BCM)
        io.setup(LED_1, io.OUT)
        io.setup(LED_2, io.OUT)

        now = datetime.now()
        timestamp = now.replace(microsecond=0).isoformat()

        picture = take_picture()
        (readings, readings_float) = meter_reader.get_readings_from_meter_image(picture)
        logging.info("Obtained readings from meter: %s => %f", readings, readings_float)
        sheets.publish_readings(sheet_id, sheet_range, timestamp, readings_float)
    except (meter_reader.ReaderError, ApplicationError) as err:
        logging.error("Error occured during obtaining of meter readings", exc_info=err)

        # Indicate in spreadsheet that there was an error that needs attention
        sheets.publish_readings(sheet_id, sheet_range, timestamp, -1)

        # Back up the picture that led to the error
        save_picture(picture, now.strftime("%Y-%m-%d-%H-%M-%S.jpg"))
        flash_indicate_error()
    finally:
        io.cleanup()


if __name__ == "__main__":
    main()
