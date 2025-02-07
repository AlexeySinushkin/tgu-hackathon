import logging
from datetime import datetime, timedelta
from time import sleep

import cv2

from found_image_processor import FoundPotholeImageProcessor
from image_utils import draw_frame_number
from pothole_analyzer import PotholeAnalyzer
from search_area import SearchArea

logging.basicConfig(level=logging.INFO, encoding='UTF-8', format='%(levelname)s: %(message)s')

#сойства видеопотока
width = 720
height = 1280
frame_rate = 30
test_video_stream = cv2.VideoCapture("resources/test_video.mp4")
test_video_search_area = SearchArea(0.2, 0.55, 0.8, 0.65)

period = 1000/frame_rate
stepping_mode = False
analyzer : PotholeAnalyzer | None = None
frame_index = 0
image_processor = FoundPotholeImageProcessor()
image_processor.start()
while True:
    if stepping_mode:
        sleep(0.2)
    loop_start = datetime.now()
    ret, original_frame = test_video_stream.read()
    if not ret:
        break
    frame_index += 1
    frame = cv2.resize(original_frame, (width, height))
    target_area = test_video_search_area.crop(frame)
    target_area_gray = cv2.cvtColor(target_area, cv2.COLOR_BGR2GRAY)
    cv2.imshow("Original", original_frame)
    if analyzer is None:
        analyzer = PotholeAnalyzer(target_area_gray.shape[1], target_area_gray.shape[0])
    analyze_result = analyzer.analyze_and_draw(target_area_gray, target_area)
    draw_frame_number(target_area, frame_index)
    cv2.imshow("Search Area", target_area)
    if analyze_result is not None:
        x, y = test_video_search_area.translate_coordinates_to_original(original_frame, analyze_result.x_left_top, analyze_result.y_left_top)
        image_processor.enqueue(original_frame, x, y, analyze_result.width, analyzer.height),
    loop_stop = datetime.now()
    spent_ms = (loop_stop - loop_start).total_seconds()*1000
    if 0 < spent_ms < period:
        sleep((period-spent_ms)/1000)


    key = cv2.waitKey(1)
    # Space
    if key == 32:
        stepping_mode = not stepping_mode
    # Esc
    if key == 27:
        cv2.destroyAllWindows()
        break
test_video_stream.release()
image_processor.stop()

