import numpy as np
import threading


class PostProcessor:
    def run(self, face_heading, face_blendshapes, time):
        return (face_heading, face_blendshapes, time)


class SmoothingPostProcessor(PostProcessor):
    def __init__(self):
        self.window = None
        self.window_length = 5
        self.idx = 0

    def run(self, face_heading, face_blendshapes, time):
        if self.window is None:
            self.window = np.array([face_heading] * self.window_length)
        else:
            self.window[self.idx] = face_heading
            self.idx = (self.idx + 1) % self.window_length

        return self.window.mean(axis=0), face_blendshapes, time

class StickyPostProcessor(PostProcessor):
    def __init__(self, minimum_stop_radius=15, maximum_stop_radius=100):
        self.minimum_stop_radius = minimum_stop_radius
        self.maximum_stop_radius = maximum_stop_radius
        self.stop_radius = self.minimum_stop_radius
        self.stopped_time = 0

        self.last_heading = np.array([-999, -999])
        self.last_timestamp = float("inf")

    def run(self, face_heading, face_blendshapes, time):
        dt = max(time - self.last_timestamp, 0)
        self.last_timestamp = time

        delta = face_heading - self.last_heading
        distance = np.linalg.norm(delta)

        if distance <= self.stop_radius:
            self.stopped_time += dt
            self.stop_radius = np.interp(
                self.stopped_time,
                [2_000, 5_000],
                [self.maximum_stop_radius, self.minimum_stop_radius],
            )
            return self.last_heading, face_blendshapes, time
        else:
            self.stopped_time = 0
            self.stop_radius = self.minimum_stop_radius
            self.last_heading = face_heading
            return face_heading, face_blendshapes, time


