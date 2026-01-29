import threading
import cv2 as cv


class VideoSource:
    def open(self):
        pass

    def read(self):
        pass

    def close(self):
        pass

    def is_opened(self):
        pass


class CameraVideoSource(VideoSource):
    def __init__(self, cam_id):
        self.cam_id = cam_id
        self.camera = cv.VideoCapture()

    def open(self):
        if self.camera.isOpened():
            return
        self.camera.open(self.cam_id)

    def read(self):
        if not self.camera.isOpened():
            raise RuntimeError("Camera is not opened")

        return self.camera.read()

    def close(self):
        if self.camera.isOpened():
            self.camera.release()

    def is_opened(self):
        return self.camera.isOpened()
