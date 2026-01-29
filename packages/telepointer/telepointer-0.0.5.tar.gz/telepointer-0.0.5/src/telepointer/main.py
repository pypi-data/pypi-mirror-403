import click
import numpy as np
from pynput.mouse import Button, Controller
import mss

import queue
import threading
import sys
import math
import time
import socket
import platform
if platform.system() == "Linux":
    import termios
    import tty
if platform.system() == "Windows":
    import msvcrt
from enum import Enum

from telepointer.third_party.landmarking.landmarker import BlazeFaceLandmarker

from telepointer.mouse_control.mouse_driver import (
    MouseDriver,
    LEFT_BUTTON,
    RIGHT_BUTTON,
    MIDDLE_BUTTON,
)
from telepointer.mouse_control.mouse_controller import (
    MouseController,
    SmoothMouseController,
    TimeScaledMouseController,
)
from telepointer.video.video_source import CameraVideoSource
from telepointer.landmarking.landmarker_processing import (
    PointerLandmarkerProcessor,
    TrackballLandmarkerProcessor,
)
from telepointer.landmarking.post_processing import (
    SmoothingPostProcessor,
    StickyPostProcessor,
)

# TODO: use a screenshots segmenter / ocr to make the cursor "magnetized" towards these features.

# TODO: add mouse controller that snaps to an angle when mouse is pressed


BUTTONS = {
    "LEFT": LEFT_BUTTON,
    "RGHT": RIGHT_BUTTON,
    "MIDL": MIDDLE_BUTTON,
}


def orchestrator(processor, mouse_ctrl, cmd_queue):
    try:
        running = True
        while running:
            cmd = cmd_queue.get()
            print(cmd)
            match cmd:
                case [Command.START]:
                    mouse_ctrl.start()
                    processor.start(mouse_ctrl.control_mouse)
                case [Command.STOP]:
                    processor.stop()
                    mouse_ctrl.stop()
                case [Command.CLICK, button]:
                    mouse_ctrl.driver.click(button)
                case [Command.PRESS, button]:
                    mouse_ctrl.driver.press(button)
                case [Command.LIFT, button]:
                    mouse_ctrl.driver.lift(button)
                case [Command.CALIBRATE]:
                    processor.calibrate()
                case [Command.QUIT]:
                    running = False
    except Exception as e:
        click.echo(e, err=True)
    except:
        click.echo("An unknown exception occured.", err=True)
    finally:
        processor.stop()
        mouse_ctrl.stop()


processor_classes = {
    "pointer": PointerLandmarkerProcessor,
    "trackball": TrackballLandmarkerProcessor,
}

post_processor_classes = {
    "s": SmoothingPostProcessor,
    "t": StickyPostProcessor,
}


@click.command()
@click.option("-c", "--calibrate", "init_calibrate", is_flag=True, default=False)
@click.option("--camera", "camera_idx", default=0)
@click.option(
    "-p",
    "--processor",
    "processor_code",
    default="trackball",
    help="One of 'trackball', 'pointer'",
)
@click.option("-s", "--control-socket", "socket_control", is_flag=True)
@click.option("-k", "--control-terminal", "terminal_control", is_flag=True, default=True)
@click.option("--post", "post_processors_arg", default="s")
def main(
    init_calibrate,
    processor_code,
    socket_control,
    terminal_control,
    camera_idx,
    post_processors_arg,
):
    with mss.mss() as sct:
        monitor = sct.monitors[0]

    camera = CameraVideoSource(camera_idx)
    landmarker = BlazeFaceLandmarker(camera)

    post_processors = [post_processor_classes[c]() for c in post_processors_arg]

    Processor = processor_classes[processor_code]
    processor = Processor(landmarker, monitor, post_processors)

    driver = MouseDriver()
    mouse_controller = SmoothMouseController(driver, 5, 15)
    time_scaled = TimeScaledMouseController(mouse_controller, 10)

    # Create Controls
    cmd_queue = queue.SimpleQueue()
    controls = []
    if socket_control:
        controls.append(SocketControl(cmd_queue))
    if terminal_control:
        controls.append(KeyControl(cmd_queue))

    click.echo("Telepointer running with configuration:")
    click.echo(f"Camera: {camera_idx}")
    click.echo(f"Landmarker: {landmarker.__class__.__name__}")
    click.echo(f"Processor: {processor.__class__.__name__}")
    click.echo(
        f"Post-Processors: {", ".join([post.__class__.__name__ for post in post_processors]) if post_processors else "none" }"
    )
    click.echo(
        f"Control methods: {", ".join([c.__class__.__name__ for c in controls]) if controls else "none" }"
    )

    if init_calibrate:
        processor.calibrate()

    for c in controls:
        c.start()

    orchestrator(processor, time_scaled, cmd_queue)

    for c in controls:
        c.stop()


class SocketControl:
    def __init__(self, cmd_queue):
        self.stop_event = threading.Event()
        self.cmd_queue = cmd_queue
        self.thread = None

        if platform.system() == "Windows":
            self.socket_family = socket.AF_INET
            self.socket_addr = ("127.0.0.1", 7154)
        else:
            self.socket_family = socket.AF_UNIX
            self.socket_addr = "\x00/tmp/telepointer-socket"

        self.server = None
        self.connection = None

    def get_command_queue(self):
        return self.cmd_queue

    def start(self):
        if not self.thread:

            def run_socket_server():
                try:
                    with socket.socket(family=self.socket_family) as server:
                        self.server = server
                        server.bind(self.socket_addr)
                        server.listen()
                        while not self.stop_event.is_set():
                            conn, addr = server.accept()
                            self.connection = conn
                            with conn:
                                result = conn.recv(4).decode("utf-8")
                                match result:
                                    case "STRT":
                                        self.cmd_queue.put([Command.START])
                                    case "STOP":
                                        self.cmd_queue.put([Command.STOP])
                                    case "CLCK":
                                        btn_code = conn.recv(4).decode("utf-8")
                                        self.cmd_queue.put(
                                            [Command.CLICK, BUTTONS[btn_code]]
                                        )
                                    case "PUSH":
                                        btn_code = conn.recv(4).decode("utf-8")
                                        self.cmd_queue.put(
                                            [Command.PRESS, BUTTONS[btn_code]]
                                        )
                                    case "LIFT":
                                        btn_code = conn.recv(4).decode("utf-8")
                                        self.cmd_queue.put(
                                            [Command.LIFT, BUTTONS[btn_code]]
                                        )
                                    case "CALI":
                                        self.cmd_queue.put([Command.CALIBRATE])
                                    case "QUIT":
                                        self.stop_event.set()

                                conn.close()
                                self.connection = None

                        server.close()
                        self.server = None
                    self.cmd_queue.put([Command.QUIT])
                except:
                    self.server = None
                    self.connection = None
                    click.echo("socket controller failed.")

            self.thread = threading.Thread(target=run_socket_server)
            self.thread.start()

    def stop(self):
        if self.thread and self.thread.is_alive():
            self.stop_event.set()
            if self.connection:
                self.connection.shutdown(socket.SHUT_RDWR)
                self.connection.close()
            if self.server:
                # For some reason Windows and/or the INET socket
                # does not like getting shutdown in this way.
                # close() works fine.
                if self.socket_family != socket.AF_INET: 
                    self.server.shutdown(socket.SHUT_RDWR)
                self.server.close()

            self.thread.join()

        self.stop_event.clear()
        self.thread = None
        self.cmd_queue = queue.SimpleQueue()


class KeyControl:
    def __init__(self, cmd_queue):
        self.stop_event = threading.Event()
        self.cmd_queue = cmd_queue
        self.thread = None

        if platform.system() == "Windows":
            self.get_char = lambda: msvcrt.getch().decode("utf-8")
        else:
            self.old_term_settings = termios.tcgetattr(sys.stdin.fileno())
            tty.setcbreak(sys.stdin.fileno())
            self.get_char = lambda: sys.stdin.read(1)

    def get_command_queue(self):
        return self.cmd_queue

    def start(self):
        if not self.thread:

            def read_keys():
                while not self.stop_event.is_set():
                    c = self.get_char().upper()
                    if c == "S":
                        self.cmd_queue.put([Command.START])
                    elif c == "P":
                        self.cmd_queue.put([Command.STOP])
                    elif c == "Q":
                        self.cmd_queue.put([Command.QUIT])
                        self.stop_event.set()

            self.thread = threading.Thread(target=read_keys, daemon=True)
            self.thread.start()

    def stop(self):
        if platform.system() != "Windows":
            termios.tcsetattr(sys.stdin.fileno(), termios.TCSADRAIN, self.old_term_settings)

        if self.thread:
            self.stop_event.set()
            self.thread = None
            self.cmd_queue = queue.SimpleQueue()


class Command(Enum):
    QUIT = 0
    START = 1
    STOP = 2
    CALIBRATE = 3
    CLICK = 4
    PRESS = 5
    LIFT = 6
