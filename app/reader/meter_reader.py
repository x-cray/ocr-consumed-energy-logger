"""Collection of functions to recognize energy meter readings"""

import os
import logging
import numpy as np
import pytesseract
import cv2
from . import ReaderError
from . import geometry

FIND_EDGES_IMAGE_HEIGHT = 900
SCRIPT_PATH = os.path.realpath(os.path.dirname(__file__))


def __curried_get_distance(pt1):
    """Returns curried version of get_euler_distance function"""
    return lambda pt2: geometry.get_euler_distance(pt1, pt2)


def __get_rectangular_contours(contours):
    """Approximates provided contours and returns only those which have 4 vertices"""
    res = []
    for contour in contours:
        peri = cv2.arcLength(contour, closed=True)
        approx = cv2.approxPolyDP(contour, 0.04 * peri, closed=True)
        hull = cv2.convexHull(approx)
        if len(hull) == 4:
            res.append(hull)
    return res


def __get_scaled_contour(contour, ratio):
    """Scales provided contour with provided ratio"""
    return np.floor_divide(contour, ratio).astype(int)


def __smooth_image(img):
    """Smoothes the image"""
    _, th1 = cv2.threshold(img, 180, 255, cv2.THRESH_BINARY)
    _, th2 = cv2.threshold(th1, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    blur = cv2.GaussianBlur(th2, (3, 3), 0)
    _, th3 = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return th3


def __remove_noise_and_smooth(img):
    """Prepares image for OCR"""
    # Apply dilation and erosion to remove some noise
    kernel = np.ones((3, 3), np.uint8)
    filtered = cv2.adaptiveThreshold(
        img.astype(np.uint8), 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 61, 8
    )
    opening = cv2.morphologyEx(filtered, cv2.MORPH_OPEN, kernel)
    closing = cv2.morphologyEx(opening, cv2.MORPH_CLOSE, kernel)
    img = __smooth_image(img)
    or_image = cv2.bitwise_or(img, closing)
    return or_image


def __recognize(roi):
    """Performs OCR and returns recognized meter readings"""
    ssd_path = os.path.join(SCRIPT_PATH, "./ssd")
    tesseract_config = (
        "--psm 8 --oem 3 -c tessedit_char_whitelist=0123456789 "
        + f"--tessdata-dir {ssd_path}"
    )
    text = pytesseract.image_to_string(roi, lang="ssd", config=tesseract_config)
    return text


def __get_edge_detection_thresholds(img):
    """Calculates the lower and upper thresholds for Canny edge detection"""
    sigma = 0.3
    median = np.median(img)
    lower = int(max(0, (1.0 - sigma) * median))
    upper = int(min(255, (1.0 + sigma) * median))
    return (lower, upper)


def __get_normalized_contour_with_dimentions(contour):
    """
    Normalizes rectangular contour for vertices to have deterministic indexes
    and calculates their width and height
    """
    contour = contour.reshape(4, 2)
    rect = cv2.minAreaRect(contour)
    box = cv2.boxPoints(rect)
    box = np.int32(box)

    # Normalize vertices by aligning them to minimum area rotated bounding box vertices
    v_tl = min(contour, key=__curried_get_distance(box[2]))
    v_tr = min(contour, key=__curried_get_distance(box[3]))
    v_bl = min(contour, key=__curried_get_distance(box[1]))
    v_br = min(contour, key=__curried_get_distance(box[0]))
    new_vertices = (
        # Account for potential rectangle rotation
        [v_tl, v_tr, v_br, v_bl]
        if rect[2] >= 45
        else [v_tr, v_br, v_bl, v_tl]
    )

    # Calculate contour dimensions
    contour = np.float32(new_vertices)
    contour_width_1 = geometry.get_euler_distance(contour[0], contour[1])
    contour_width_2 = geometry.get_euler_distance(contour[3], contour[2])
    contour_height_1 = geometry.get_euler_distance(contour[0], contour[3])
    contour_height_2 = geometry.get_euler_distance(contour[1], contour[2])
    contour_width_candidate = int(max(contour_width_1, contour_width_2))
    contour_height_candidate = int(max(contour_height_1, contour_height_2))
    contour_width = max(contour_width_candidate, contour_height_candidate)
    contour_height = min(contour_width_candidate, contour_height_candidate)

    return (contour, (contour_width, contour_height))


def __get_binarized_readings_roi(display_img, display_width, display_height):
    """Returns cropped binarized image of readings suitable for OCR"""
    # Prepare image for OCR with tesseract
    ocr_image = display_img.copy()
    ocr_image = cv2.cvtColor(ocr_image, cv2.COLOR_BGR2GRAY)
    ocr_image = __remove_noise_and_smooth(ocr_image)

    # Knowing the location of the readings within the LCD ROI we can extract the readings ROI
    readings_left_edge = int(display_width * 0.144)
    readings_right_edge = int(display_width * 0.965)
    readings_top_edge = int(display_height * 0.367)
    readings_bottom_edge = int(display_height * 0.650)
    readings_roi = ocr_image[
        readings_top_edge:readings_bottom_edge, readings_left_edge:readings_right_edge
    ]

    # Pad image with white border to improve OCR accuracy
    readings_roi = cv2.copyMakeBorder(
        readings_roi, 20, 20, 20, 20, cv2.BORDER_CONSTANT, value=(255, 255, 255)
    )

    return readings_roi


def get_readings_from_meter_image(img):
    """
    Searches for meter readings on the image and returns recognized value

    Parameters
    ----------
    img : Numpy array
        Image with a photo of the meter
    """
    find_display_image = img.copy()
    find_display_image = cv2.cvtColor(find_display_image, cv2.COLOR_BGR2GRAY)

    # Resize the image for more accurate contour detection
    (height, width) = find_display_image.shape[:2]
    ratio = FIND_EDGES_IMAGE_HEIGHT / float(height)
    dim = (int(width * ratio), FIND_EDGES_IMAGE_HEIGHT)
    find_display_image = cv2.resize(
        find_display_image, dim, interpolation=cv2.INTER_AREA
    )

    # Apply blur and detect edges
    find_display_image = cv2.GaussianBlur(find_display_image, (3, 3), 0)
    (lower, upper) = __get_edge_detection_thresholds(find_display_image)
    edged = cv2.Canny(find_display_image, lower, upper)

    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    dilated = cv2.dilate(edged, kernel, iterations=2)

    # Find contours on the dilated image
    contours, _ = cv2.findContours(dilated, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    rectangular_contours = __get_rectangular_contours(contours)

    logging.info(
        "Found %d total contours out of which %d are rectangular",
        len(contours),
        len(rectangular_contours),
    )

    scaled_normalized_contours = [
        __get_normalized_contour_with_dimentions(__get_scaled_contour(c, ratio))
        for c in rectangular_contours
    ]

    # Assume that display contour is the rectangular contour which
    # aspect ratio is the closest to 1.72
    sorted_contours = sorted(
        scaled_normalized_contours,
        # Handle edge cases to prevent division by zero with sufficiently
        # large number to go to the end of the list
        key=lambda nc: abs(1.72 - nc[1][0] / nc[1][1]) if nc[1][1] else 100,
    )
    display_contour = next(iter(sorted_contours), None)

    if not display_contour:
        raise ReaderError("Unable to find display contour")

    logging.info("Located display contour: %s", display_contour)

    (display_width, display_height) = display_contour[1]
    display_dst_pts = np.float32(
        [
            [display_width, display_height],
            [0, display_height],
            [0, 0],
            [display_width, 0],
        ]
    )

    # Extract LCD image and perform perspective transformation
    transform_matrix = cv2.getPerspectiveTransform(display_contour[0], display_dst_pts)
    warp = cv2.warpPerspective(
        img, transform_matrix, (display_width, display_height), flags=cv2.INTER_LINEAR
    )

    # Perform OCR
    readings_roi = __get_binarized_readings_roi(warp, display_width, display_height)
    readings = __recognize(readings_roi).strip()
    readings_float = float(readings) / 1000

    if readings_float < 0.1:
        raise ReaderError(
            f"Incorrect readings: {readings_float}, "
            + "most likely display contour was not properly identified"
        )

    return (readings, readings_float)
