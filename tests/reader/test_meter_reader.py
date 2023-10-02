import os
import cv2
import pytest
from app.reader import meter_reader, ReaderError

SCRIPT_PATH = os.path.realpath(os.path.dirname(__file__))


class TestMeterReader:
    @pytest.mark.parametrize(
        "image_path, expected_readings",
        [
            ("../../img/readings-1.jpg", 92.472),
            ("../../img/readings-2.jpg", 92.469),
            ("../../img/readings-3.jpg", 92.647),
            ("../../img/readings-4.jpg", 92.469),
            ("../../img/readings-5.jpg", 92.469),
        ],
    )
    def test_readings_detection_and_ocr(self, image_path, expected_readings):
        # Arrange
        image = cv2.imread(os.path.join(SCRIPT_PATH, image_path))
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # Act
        readings = meter_reader.get_readings_from_meter_image(image)

        # Assert
        assert readings == expected_readings

    def test_wrong_image_exception(self):
        # Arrange
        image = cv2.imread(os.path.join(SCRIPT_PATH, "../../img/rpi-1.jpg"))
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # Assert
        with pytest.raises(
            ReaderError,
            match=r"Incorrect readings: 0\.\d+, most likely display contour was not properly identified",
        ):
            meter_reader.get_readings_from_meter_image(image)
