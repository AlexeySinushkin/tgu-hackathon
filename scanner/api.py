import unittest
from datetime import datetime

import cv2
import requests
import logging

from image_utils import opencv_to_base64


base_url = "http://176.119.158.23:8001"
upload_url = f"{base_url}/upload-gps-data"
date_format = "%Y-%m-%d"



class FakeGPSCoordinateService:
    def __init__(self):
        self.gps_coordinate_index:int = 0
        self.gps_coordinates = [
            (52.226479, 104.303981),
            (52.226713, 104.303622),
            (52.227018, 104.303144),
            (52.227547, 104.302495),
            (52.227797, 104.302270),
            (52.228106, 104.302538),
            (52.228395, 104.302887),
            (52.228861, 104.303761)
        ]
    def get_current_position(self):
        result = self.gps_coordinates[self.gps_coordinate_index]
        self.gps_coordinate_index+=1
        if self.gps_coordinate_index==len(self.gps_coordinates):
            self.gps_coordinate_index=0
        return result

gps_coordinates_service = FakeGPSCoordinateService()

class ImageForUpload:
    latitude: float
    longitude: float
    event_date: datetime
    x_top_left: int
    y_top_left: int
    def __init__(self, image, x, y, width, height):
        latitude, longitude = gps_coordinates_service.get_current_position()
        self.latitude = latitude
        self.longitude = longitude
        self.event_date = datetime.now()
        self.image = image
        self.x_top_left = x
        self.y_top_left = y
        self.width = width
        self.height = height


def upload(image: ImageForUpload):
    body = {
        "latitude": image.latitude,
        "longitude": image.longitude,
        "date": image.event_date.strftime(date_format),
        "img": opencv_to_base64(image.image),
        "x_top_left": image.x_top_left,
        "y_top_left": image.y_top_left
    }
    logging.debug("attempt to send image")
    response = requests.post(upload_url, json=body)
    if response.status_code == 200:
        print(response.json())  # Parse JSON response
    else:
        print(f"Error: {response.status_code}")
        logging.error(response.text)

class UploadTest(unittest.TestCase):
    def test_upload(self):
        image = cv2.imread("resources/upload_test.png")
        image_for_upload = ImageForUpload(image, 298, 576, 534,938)
        upload(image_for_upload)