from datetime import datetime, timedelta
from time import sleep

import cv2
from search_area import SearchArea
#сойства видеопотока
width = 720
height = 1280
frame_rate = 30
test_video_stream = cv2.VideoCapture("resources/test_video.mp4")
test_video_search_area = SearchArea(0.2, 0.55, 0.8, 0.7)

period = 1000/frame_rate
stepping_mode = False
while True:
    if stepping_mode:
        sleep(0.1)
    loop_start = datetime.now()
    ret, original_frame = test_video_stream.read()
    if not ret:
        break
    frame = cv2.resize(original_frame, (width, height))
    target_area = test_video_search_area.crop(frame)
    target_area_gray = cv2.cvtColor(target_area, cv2.COLOR_BGR2GRAY)
    cv2.imshow("Original", original_frame)
    cv2.imshow("Search Area", target_area_gray)

    loop_stop = datetime.now()
    spent_ms = (loop_stop - loop_start).total_seconds()*1000
    if 0 < spent_ms < period:
        sleep((period-spent_ms)/1000)

    # Esc
    key = cv2.waitKey(1)
    if key == 32:
        stepping_mode = not stepping_mode
    if key == 27:
        cv2.destroyAllWindows()
        break
test_video_stream.release()

