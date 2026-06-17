import cv2
import os
from config import Config


class VideoStream:
    def __init__(self, source=Config.SOURCE):
        self.source = source
        self.cap = None
        self.is_file = False

    def open(self):
        if isinstance(self.source, str) and os.path.isfile(self.source):
            self.is_file = True
        self.cap = cv2.VideoCapture(self.source)
        if not self.cap.isOpened():
            raise RuntimeError(f"Cannot open source: {self.source}")
        return self.cap

    def read(self):
        if self.cap is None:
            return False, None
        return self.cap.read()

    def release(self):
        if self.cap:
            self.cap.release()

    def get_fps(self):
        return self.cap.get(cv2.CAP_PROP_FPS) if self.cap else 0

    def get_frame_count(self):
        return int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT)) if self.cap else 0

    @staticmethod
    def resize_frame(frame, width=Config.FRAME_WIDTH, height=Config.FRAME_HEIGHT):
        return cv2.resize(frame, (width, height))
