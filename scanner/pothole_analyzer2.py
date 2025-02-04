import unittest

import cv2
import numpy as np

num_bins = 64
color_range = [0, 64]

class PotholeAnalyzer2:
    width: int
    height: int
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.mask = np.zeros((height, width), dtype=np.uint8)
        delta = width/5
        pts = np.array([[0, 0], [delta, 0], [width-delta, 0],  [width-1, height-1]], np.int32)
        self.pts = pts.reshape((-1, 1, 2))
        cv2.fillPoly(self.mask, [self.pts], 255)
        self.minDist = int(height / 30)
        self.minRadius = int(height / 10)
        self.maxRadius = int(height / 5)

    def analyze_and_draw(self, image_for_analyze, image_for_draw):
        image = image_for_analyze
        image = cv2.bitwise_and(image, image, mask=self.mask)
        image = cv2.GaussianBlur(image, (7, 7), 2)
        hist = cv2.calcHist([image], [0], None, [num_bins], color_range)
        cv2.normalize(hist, hist, alpha=0, beta=1, norm_type=cv2.NORM_MINMAX)
        #ищем цвета которых больше 20% и убираем их
        indices = np.where(hist > 0.02)[0]
        if indices is not None:
            for i in indices:
                mask = (image == i)
                image[mask]=0

        circles = cv2.HoughCircles(image, cv2.HOUGH_GRADIENT, 1, self.minDist,
                                   param1=80, param2=20,
                                   minRadius=self.minRadius, maxRadius=self.maxRadius)
        if circles is not None:
            circles = np.around(circles).astype('uint16')
            for x, y, r in circles[0, :]:
                cv2.circle(image_for_draw, (x, y), r, (0, 255, 0), 2)

class Algo2Test(unittest.TestCase):
    def test_extract(self):
        image = cv2.imread("resources/algo2.png")
        mask = np.zeros(image.shape[:2], dtype=np.uint8)
        # 1694 932
        y1 = 480
        y2 = 660
        x1 = 360
        x2 = 1538
        pts = np.array([[360, 660], [700, 480], [1165, 480],  [1538, 660]], np.int32)
        pts = pts.reshape((-1, 1, 2))

        # Draw the polygon on the mask
        cv2.fillPoly(mask, [pts], 255)
        # Apply the mask to extract the region
        result = cv2.bitwise_and(image, image, mask=mask)
        result = result[y1:y2, x1:x2]
        imageGray = cv2.cvtColor(result, cv2.COLOR_BGR2GRAY)
        imageGray = cv2.GaussianBlur(imageGray, (7, 7), 2)
        hist = cv2.calcHist([imageGray], [0], None, [num_bins], color_range)
        cv2.normalize(hist, hist, alpha=0, beta=1, norm_type=cv2.NORM_MINMAX)
        #ищем цвета которых больше 20% и убираем их
        indices = np.where(hist > 0.02)[0]
        if indices is not None:
            for i in indices:
                mask = (imageGray == i)
                imageGray[mask]=0

        height = imageGray.shape[0]
        minDist = int(height / 30)
        minRadius = int(height / 10)
        maxRadius = int(height / 5)
        circles = cv2.HoughCircles(imageGray, cv2.HOUGH_GRADIENT, 1, minDist,
                                   param1=80, param2=20,
                                   minRadius=minRadius, maxRadius=maxRadius)
        if circles is not None:
            circles = np.around(circles).astype('uint16')
            for x, y, r in circles[0, :]:
                cv2.circle(imageGray, (x, y), r, (0, 255, 0), 2)
        cv2.imshow("Extracted Region", imageGray)
        key = cv2.waitKey(0)
        # Esc
        if key == 27:
            cv2.destroyAllWindows()