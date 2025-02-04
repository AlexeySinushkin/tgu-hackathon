from datetime import datetime, timedelta
from time import sleep

import cv2

from image_utils import draw_frame_number
from pothole_analyzer2 import PotholeAnalyzer2
from search_area import SearchArea

#сойства видеопотока
width = int(1920/2)
height = int(1072/2)
frame_rate = 30
test_video_stream = cv2.VideoCapture("resources/test_video2.mp4")
test_video_search_area = SearchArea(286/1606, 352/892, 1469/1606, 632/892)

period = 1000/frame_rate
stepping_mode = False
analyzer : PotholeAnalyzer2 | None = None
frame_index = 0
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
        analyzer = PotholeAnalyzer2(target_area_gray.shape[1], target_area_gray.shape[0])
    analyzer.analyze_and_draw(target_area_gray, target_area_gray)
    draw_frame_number(target_area, frame_index)
    cv2.imshow("Search Area", target_area)


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

