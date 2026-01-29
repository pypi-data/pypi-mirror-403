from enum import Enum
from pynput.mouse import Button, Controller


NO_BUTTON = 0
LEFT_BUTTON = 1 << 0
RIGHT_BUTTON = 1 << 1
MIDDLE_BUTTON = 1 << 2


class MouseDriver:
    def __init__(self):
        self.controller = Controller()
        self.currentState = NO_BUTTON

    def move(self, dx, dy):
        self.controller.move(dx, dy)

    def click(self, buttons):
        if buttons & LEFT_BUTTON:
            self.controller.click(Button.left)
        if buttons & RIGHT_BUTTON:
            self.controller.click(Button.right)
        if buttons & MIDDLE_BUTTON:
            self.controller.click(Button.middle)

    def press(self, buttons):
        self.set_pressed_buttons(self.currentState | buttons)

    def lift(self, buttons):
        self.set_pressed_buttons(self.currentState & ~buttons)

    def pressed_buttons(self):
        return self.currentState

    def set_pressed_buttons(self, buttons):
        changed = self.currentState ^ buttons

        if changed & LEFT_BUTTON:
            if buttons & LEFT_BUTTON:
                self.controller.press(Button.left)
            else:
                self.controller.release(Button.left)

        if changed & RIGHT_BUTTON:
            if buttons & RIGHT_BUTTON:
                self.controller.press(Button.right)
            else:
                self.controller.release(Button.right)

        if changed & MIDDLE_BUTTON:
            if buttons & MIDDLE_BUTTON:
                self.controller.press(Button.middle)
            else:
                self.controller.release(Button.middle)

        self.currentState = buttons

    def position(self):
        return self.controller.position

    def set_position(self, x, y):
        self.controller.position = (x, y)
