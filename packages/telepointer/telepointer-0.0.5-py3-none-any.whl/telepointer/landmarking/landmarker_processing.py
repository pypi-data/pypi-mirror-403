import numpy as np
from threading import Thread, Event
import sys
import time
from scipy.spatial.transform import Rotation as Rot

BROW_INNER_UP = 3
BROW_OUTER_UP_LEFT = 4
BROW_OUTER_UP_RIGHT = 5
CHEEK_PUFF = 6
EYE_BLINK_LEFT = 9
EYE_BLINK_RIGHT = 10
EYE_SQUINT_LEFT = 19
EYE_SQUINT_RIGHT = 20
MOUTH_PUCKER = 38


class LandmarkerProcessor:
    def __init__(self, landmarker, monitor, post_processors=[]):
        monitor["right"] = monitor["left"] + monitor["width"]
        monitor["bottom"] = monitor["top"] + monitor["height"]
        self.monitor = monitor
        self.landmarker = landmarker
        self.post_processors = post_processors

        if "win32" in sys.platform:
            # for some reason sometimes the monotonic clock on windows
            # gives the same value if delay is too short
            self.clk_period = 20
        else:
            self.clk_period = 1

    def extract_facial_features(self, face_blendshapes):
        return {
            "brow_up": max(
                face_blendshapes[BROW_INNER_UP],
                face_blendshapes[BROW_OUTER_UP_LEFT],
                face_blendshapes[BROW_OUTER_UP_RIGHT],
            ),
            "cheek_puff": face_blendshapes[CHEEK_PUFF],
            "left_blink": face_blendshapes[EYE_BLINK_LEFT],
            "left_squint": face_blendshapes[EYE_SQUINT_LEFT],
            "mouth_pucker": face_blendshapes[MOUTH_PUCKER],
        }

    def _process_landmark_result(self, face_transform_matrix, face_blendshapes, time):
        pass

    def is_started(self):
        return self.landmarker.is_started()

    def start(self, callback, raw=False):

        def landmarker_callback(face_transform, face_blendshapes, time):
            processed_result = self._process_landmark_result(
                face_transform, face_blendshapes, time
            )

            for post_processor in self.post_processors:
                processed_result = post_processor.run(*processed_result)

            callback(*processed_result)

        self.landmarker.start(self.clk_period, landmarker_callback)

    def stop(self):
        self.landmarker.stop()


class PointerLandmarkerProcessor(LandmarkerProcessor):
    def __init__(self, landmarker, monitor, post_processors=[]):
        config = {
            "calibration": {
                "corner_top_right": [1, 1],
                "corner_bottom_left": [20, -20],
            },
        }
        super().__init__(landmarker, monitor, post_processors)
        self.load_config(config)

    def load_config(self, config):
        self.bounds = (
            config["calibration"]["corner_bottom_left"],
            config["calibration"]["corner_top_right"],
        )

    def extract_raw_face_heading(self, face_transform_matrix):
        matrix = face_transform_matrix
        R = matrix[:3, :3]
        t = matrix[:3, 3]

        direction = R @ np.array([0, 0, 1])

        s = -t[2] / direction[2]

        intersect = t + s * direction

        plane_point = intersect[:2]
        return plane_point

    def extract_face_heading(self, face_transform_matrix):
        plane_point = self.extract_raw_face_heading(face_transform_matrix)
        return np.array(
            [
                np.interp(
                    plane_point[0],
                    [self.bounds[0][0], self.bounds[1][0]],
                    [self.monitor["right"], self.monitor["left"]],
                ),
                np.interp(
                    plane_point[1],
                    [self.bounds[0][1], self.bounds[1][1]],
                    [self.monitor["bottom"], self.monitor["top"]],
                ),
            ]
        )

    def _process_landmark_result(self, face_transform_matrix, face_blendshapes, time):
        return (
            self.extract_face_heading(face_transform_matrix),
            self.extract_facial_features(face_blendshapes),
            time,
        )

    def calibrate(self):
        config = {
            "calibration": {"corner_top_right": None, "corner_bottom_left": None},
        }

        top_right_event = Event()
        bot_left_event = Event()
        capture_event = Event()

        def callback(face_transform_matrix, face_blendshapes, time):
            raw_face_heading = self.extract_raw_face_heading(face_transform_matrix)
            if bot_left_event.is_set():
                config["calibration"]["corner_bottom_left"] = list(raw_face_heading)
                bot_left_event.clear()
                capture_event.set()
            elif top_right_event.is_set():
                config["calibration"]["corner_top_right"] = list(raw_face_heading)
                top_right_event.clear()
                capture_event.set()

        self.landmarker.start(self.clk_period, callback)
        print("Look at top right corner - 3 seconds remain")
        time.sleep(3)
        top_right_event.set()
        capture_event.wait()
        capture_event.clear()
        print("Top right corner captured")

        print("Look at bottom left corner - 3 seconds remain")
        time.sleep(3)
        bot_left_event.set()
        capture_event.wait()
        capture_event.clear()
        print("Bottom left corner captured")

        self.landmarker.stop()
        self.load_config(config)
        print(f"Calibration complete. New config: {config}")


class TrackballLandmarkerProcessor(LandmarkerProcessor):
    def __init__(self, landmarker, monitor, post_processors=[]):
        super().__init__(landmarker, monitor, post_processors)
        self.heading = np.array(
            [
                (monitor["left"] + monitor["right"]) // 2,
                (monitor["top"] + monitor["bottom"]) // 2,
            ]
        )
        self.last_transform = None
        self.sensitivity = 3_000 * np.array([1, -1])

    def _process_landmark_result(self, face_transform_matrix, face_blendshapes, time):
        if self.last_transform is None:
            self.last_transform = face_transform_matrix

        rotational_diff = Rot.from_matrix(
            face_transform_matrix[:3, :3] @ np.linalg.inv(self.last_transform[:3, :3])
        )
        angles = rotational_diff.as_euler("YXZ")
        delta = -angles[:2] * self.sensitivity
        self.heading += delta.astype("int64")
        self.last_transform = face_transform_matrix

        return (self.heading.copy(), self.extract_facial_features(face_blendshapes), time)

    def calibrate(self):
        self.heading = np.array(
            [
                (self.monitor["left"] + self.monitor["right"]) // 2,
                (self.monitor["top"] + self.monitor["bottom"]) // 2,
            ]
        )
