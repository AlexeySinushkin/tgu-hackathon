import threading
import time

from api import ImageForUpload, upload


class FoundPotholeImageProcessor(threading.Thread):
    def __init__(self):
        super().__init__()
        self.queue = []
        self.do_run = True

    def enqueue(self, image, x, y, width, height):
        self.queue.append(ImageForUpload(image, x, y, width, height))

    def run(self):
        while self.do_run:
            if len(self.queue) > 0:
                upload(self.queue.pop(0))
            else:
                time.sleep(1)

    def stop(self):
        self.do_run = False

    def await_and_stop(self):
        while self.do_run:
            if len(self.queue) > 0:
                time.sleep(1)
        self.stop()
