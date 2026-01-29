import numpy as np
import queue
import threading

# TODO: Mouse controller that scales movement quadratically

# TODO: add an option for automatic mouse teleport to 0,0 when stopped so that it looks like the cursor dissapears when stopped (DOES NOT WORK RN)

# TODO:

MIN_INACTIVE_RADIUS = 25
MAX_INACTIVE_RADIUS = 100


class MouseController:
    def __init__(self, driver, auto_clear=True):
        self.driver = driver
        self.auto_clear = auto_clear

    def control_mouse(self, face_pos, features, timestamp):
        delta = face_pos - self.driver.position()
        self.driver.move(delta[0], delta[1])

    def start(self):
        pass

    def stop(self):
        self.driver.set_pressed_buttons(0)
        if self.auto_clear:
            self.driver.set_position(0, 0)


class SmoothMouseController(MouseController):
    def __init__(self, driver, speed, inactive_radius):
        super().__init__(driver)

        self.speed = speed

        self.in_radius_time = 0

        self.last_timestamp = None

    def control_mouse(self, face_pos, features, timestamp):
        if not self.last_timestamp:
            self.last_timestamp = timestamp
            return

        # calc dt
        dt = max(timestamp - self.last_timestamp, 0)
        self.last_timestamp = timestamp

        # Movement
        delta = face_pos - self.driver.position()

        move_delta = delta * self.speed * dt / 1000
        self.driver.move(move_delta[0], move_delta[1])


class TimeScaledMouseController(MouseController):
    def __init__(self, controller, target_dt_ms):
        super().__init__(controller.driver)
        self.controller = controller

        self.target_dt = target_dt_ms / 1000
        self.thread = None
        self.input_queue = queue.SimpleQueue()
        self.stop_event = threading.Event()

    def control_mouse(self, *args):
        self.input_queue.put(args)

    def start(self):
        if not self.thread:

            def scale_input():
                try:
                    *controller_args, timestamp = self.input_queue.get(timeout=1)
                    self.controller.control_mouse(*controller_args, timestamp)
                except queue.Empty:
                    return

                while not self.stop_event.is_set():
                    try:
                        *controller_args, timestamp = self.input_queue.get(
                            timeout=self.target_dt
                        )
                    except queue.Empty:
                        timestamp += self.target_dt * 1000
                    self.controller.control_mouse(*controller_args, timestamp)

            self.thread = threading.Thread(target=scale_input)
            self.thread.start()

    def stop(self):
        if self.thread:
            self.stop_event.set()
            self.thread.join()
            self.stop_event.clear()
            self.thread = None

            self.queue = queue.Queue()
