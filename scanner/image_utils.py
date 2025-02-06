import base64
import unittest

import cv2
import numpy as np


def draw_frame_number(image, frame_number):
    position = (20, 30)  # X, Y coordinates (bottom-left of text)
    font = cv2.FONT_HERSHEY_SIMPLEX  # Font type
    font_scale = 1  # Font size
    color = (0, 255, 0)  # Green color in BGR
    thickness = 2  # Thickness of the text
    line_type = cv2.LINE_AA  # Anti-aliased text

    # Add text to image
    cv2.putText(image, str(frame_number), position, font, font_scale, color, thickness, line_type)

def draw_correl_value(image, corell_value, x, y_bl):
    font = cv2.FONT_HERSHEY_SIMPLEX  # Font type
    font_scale = 0.3  # Font size
    color = (0, 255, 0)  # Green color in BGR
    thickness = 1  # Thickness of the text
    line_type = cv2.LINE_AA  # Anti-aliased text

    # Add text to image
    cv2.putText(image, str(corell_value), (x, y_bl), font, font_scale, color, thickness, line_type)

def opencv_to_base64(image):
    # Encode image as PNG
    _, buffer = cv2.imencode('.png', image)

    # Convert to Base64
    base64_str = base64.b64encode(buffer).decode('utf-8')
    return base64_str



class Base64Test(unittest.TestCase):
    def test_base64(self):
        image = cv2.imread("resources/upload_test.png")
        image_str = opencv_to_base64(image)
        decoded_bytes = np.frombuffer(base64.b64decode(image_str), dtype=np.uint8)
        decoded_image = cv2.imdecode(decoded_bytes, cv2.IMREAD_COLOR)
        cv2.imshow("encode correct", decoded_image)
        cv2.waitKey(0)
