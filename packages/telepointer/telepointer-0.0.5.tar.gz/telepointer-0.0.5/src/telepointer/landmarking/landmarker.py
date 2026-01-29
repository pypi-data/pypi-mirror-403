import time
import threading
import click


class Landmarker:
    def __init__(self, vid_source):
        self.quit_event = threading.Event()
        self.video = vid_source
        self.thread = None

    def stop(self):
        self.quit_event.set()
        self.video.close()
        if self.thread:
            self.thread.join()
        self.quit_event.clear()

    def start(self, clk_period_ms, callback):
        if self.thread and self.thread.is_alive():
            raise RuntimeError("Thread already started")

        self.thread = threading.Thread(target=self.landmark_thread, args=(self._create_landmarker(callback), clk_period_ms))
        self.thread.start()

    def is_started(self):
        return self.thread and self.thread.is_alive()

    def landmark_thread(self, created_landmarker, clk_period_ms):
        clk_period = clk_period_ms / 1000
        self.video.open()

        start_time = time.monotonic_ns()

        with created_landmarker as landmarker:
            while self.video.is_opened() and not self.quit_event.is_set():
                success, raw_frame = self.video.read()
                if not success:
                    break

                self._run_async(
                    landmarker,
                    raw_frame,
                    (time.monotonic_ns() - start_time) // 1_000_000,
                )
                time.sleep(clk_period)

    def _create_landmarker(self, callback):
        pass

    def _run_async(self, landmarker, image, timestamp):
        pass
