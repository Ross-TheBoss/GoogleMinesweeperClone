import math
from abc import ABC
from enum import Enum
from typing import Optional, Union, Type, TypeVar

import pyglet

pyglet.options["win32_gdi_font"] = True
from pyglet.shapes import Triangle, Rectangle
from pyglet.window import Window

from minesweeper.constants import Difficulty, DIFFICULTY_SETTINGS

from pyglet.sprite import Sprite
from pyglet.text import Label

from minesweeper import shapes
import os

from pyglet import font
from pyglet.graphics import Group, Batch


class Colour(tuple, Enum):
    _hint = tuple[int, int, int, int]

    WHITE: _hint = (255, 255, 255, 255)
    HEADER_GREEN: _hint = (74, 117, 44, 255)
    DIFFICULTY_SELECTED: _hint = (229, 229, 229, 255)
    DIFFICULTY_LABEL: _hint = (48, 48, 48, 255)


# Specify resource paths.
BASEDIR = os.path.dirname(os.path.abspath(__file__))

pyglet.resource.path = [os.path.join(BASEDIR, "assets"),
                        os.path.join(BASEDIR, "assets", "numbers"),
                        os.path.join(BASEDIR, "assets", "fonts", "Roboto")]
pyglet.resource.reindex()

flag_image = pyglet.resource.image("flag_icon.png")
flag_image.width = 38
flag_image.height = 38

clock_image = pyglet.resource.image("clock_icon.png")
clock_image.width = 38
clock_image.height = 38

tutorial_flag_image = pyglet.resource.image("tutorial_desktop_flag.png")
tutorial_dig_image = pyglet.resource.image("tutorial_desktop_dig.png")

checkmark_image = pyglet.resource.image("checkmark.png")

mute_image = pyglet.resource.image("volume_off_white.png")
mute_image.width = 30
mute_image.height = 30

unmute_image = pyglet.resource.image("volume_up_white.png")
unmute_image.width = 30
unmute_image.height = 30

# Load fonts
# Font weight 400
pyglet.resource.add_font("Roboto-Regular.ttf")
roboto = font.load("Roboto")

# Font weight 500
pyglet.resource.add_font("Roboto-Medium.ttf")
roboto_medium = font.load("Roboto Medium")

# Font weight 700
pyglet.resource.add_font("Roboto-Bold.ttf")
roboto_bold = font.load("Roboto Bold")

# Font weight 900
pyglet.resource.add_font("Roboto-Black.ttf")
roboto_black = font.load("Roboto Black")


class Anchor(float, Enum):
    BOTTOM = LEFT = 0.0
    CENTER = 0.5
    TOP = RIGHT = 1.0


class AnchorGroup(Group):
    def __init__(self, window, x, y, width, height,
                 anchor_x: Anchor = Anchor.CENTER, anchor_y: Union[Anchor, float] = Anchor.CENTER,
                 order: int = 0, parent: Optional[Group] = None):
        super().__init__(order, parent)
        self._window = window

        self.x = x
        self.y = y
        self.width = width
        self.height = height

        self._anchor_x = anchor_x
        self._anchor_y = anchor_y

    def __eq__(self, other):
        return (self.__class__ is other.__class__ and
                self._order == other.order and
                self.parent == other.parent and
                self._anchor_x == other._anchor_x and
                self._anchor_y == other._anchor_y)

    def __hash__(self):
        # self.x, self.y, self.width and self.height are variable, so they cannot be hashed.
        return hash((self._order, self.parent,
                     self._anchor_x, self._anchor_y))

    def __repr__(self):
        return f"{self.__class__.__name__}(anchor_x={self._anchor_x}, anchor_y={self._anchor_y}, order={self._order})"

    def set_state(self):
        x = self.x - (self.width * self._anchor_x)
        y = self.y - (self.height * self._anchor_y)

        view_matrix = self._window.view.translate((x, y, 0))

        self._window.view = view_matrix

    def unset_state(self):
        x = self.x - (self.width * self._anchor_x)
        y = self.y - (self.height * self._anchor_y)

        view_matrix = self._window.view.translate((-x, -y, 0))

        self._window.view = view_matrix

    def transform_point(self, x, y):
        parent = self
        while isinstance(parent, Group):
            parent = parent.parent
            if parent is None:
                break

            if isinstance(parent, AnchorGroup):
                x, y = parent.transform_point(x, y)
                break

        x -= self.x - (self.width * self._anchor_x)
        y -= self.y - (self.height * self._anchor_y)

        return x, y

    @property
    def anchor_x(self):
        return self._anchor_x

    @property
    def anchor_y(self):
        return self._anchor_y


# Modifying widgets from pyglet.gui to account for anchor groups.
W = TypeVar("W", bound=pyglet.gui.WidgetBase)


def anchor_group_decorator(cls: Type[W]) -> Type[W]:
    def _check_hit(self, x, y):
        parent = self._user_group
        while parent is not None:
            if isinstance(self._user_group, AnchorGroup):
                x, y = self._user_group.transform_point(x, y)
                break
            else:
                parent = parent.parent

        return self._x < x < self._x + self._width and self._y < y < self._y + self._height

    cls._check_hit = _check_hit

    return cls


ToggleButton = anchor_group_decorator(pyglet.gui.ToggleButton)


class Tutorial:
    width = 120
    height = 120

    def __init__(self, window, x, y, batch: Optional[Batch] = None, group: Optional[Group] = None):
        super().__init__()

        self.batch = batch or pyglet.graphics.get_default_batch()
        self.group = AnchorGroup(window, x, y, self.width, self.height, order=1, parent=group)

        self.animation = pyglet.image.Animation.from_image_sequence([tutorial_dig_image, tutorial_flag_image],
                                                                    duration=3, loop=True)
        self.sprite = Sprite(self.animation, 10, 17,
                             batch=self.batch, group=Group(1, self.group))
        self.sprite.scale = 100 / self.sprite.width

        self.background = shapes.RoundedRectangle(0, 0, self.width, self.height, radius=16,
                                                  color=(0, 0, 0, 153),
                                                  batch=self.batch, group=Group(0, self.group))

    def on_first_interaction(self):
        self.group.visible = False


class Counters:
    def __init__(self, window, difficulty: Difficulty, batch: Optional[Batch] = None, group: Optional[Group] = None):
        super().__init__()

        self.batch = batch or pyglet.graphics.get_default_batch()
        self.group = AnchorGroup(window, window.width * 0.5, window.height,
                                 window.width * 0.35, 60,
                                 anchor_y=Anchor.TOP, parent=group)

        self._window = window

        cumulative_x = 0

        flag_image.width = 38
        flag_image.height = 38
        self.flag_icon = Sprite(flag_image, 0, 0, batch=self.batch,
                                group=AnchorGroup(window, 0, 30, 38, 38,
                                                  anchor_y=Anchor.CENTER, anchor_x=Anchor.LEFT,
                                                  parent=self.group))
        cumulative_x += 38

        self.flag_counter = Label(str(DIFFICULTY_SETTINGS[difficulty].mines), font_name="Roboto", font_size=15,
                                  bold=True,
                                  x=cumulative_x + 3, y=30 + 1, width=self.group.width * 0.2, height=20,
                                  anchor_y="center",
                                  batch=self.batch, group=self.group)
        cumulative_x += 3 + self.flag_counter.width

        clock_image.width = 38
        clock_image.height = 38
        self.clock_icon = Sprite(clock_image, cumulative_x, 0,
                                 batch=self.batch,
                                 group=AnchorGroup(window, 0, 30, 38, 38,
                                                   anchor_y=Anchor.CENTER, anchor_x=Anchor.LEFT,
                                                   parent=self.group))
        cumulative_x += 38

        self.clock_counter = Label("000", font_name="Roboto", font_size=15, bold=True,
                                   x=cumulative_x + 3, y=30 + 1, width=self.group.width * 0.2, height=20,
                                   anchor_y="center",
                                   batch=self.batch, group=self.group)

    def repack(self):
        self.group.x = self._window.width * 0.5
        self.group.y = self._window.height
        self.group.width = self._window.width * 0.35

        cumulative_x = 0
        # Flag Icon
        cumulative_x += 38

        # Flag Counter
        self.flag_counter.x = cumulative_x + 3
        self.flag_counter.width = self.group.width * 0.2
        cumulative_x += 3 + self.flag_counter.width

        # Clock Icon
        self.clock_icon.x = cumulative_x
        cumulative_x += 38

        # Clock Counter
        self.clock_counter.x = cumulative_x + 3
        self.clock_counter.width = self.group.width * 0.2

    def on_flag_place(self, checkerboard):
        self.flag_counter.text = str(checkerboard.mines - len(checkerboard.flags))

    def on_flag_remove(self, checkerboard):
        self.flag_counter.text = str(checkerboard.mines - len(checkerboard.flags))

    def on_second_pass(self):
        seconds = int(self.clock_counter.text) + 1
        self.clock_counter.text = f"{seconds:0>3}"


class MuteButton(pyglet.event.EventDispatcher):
    def __init__(self, window, batch: Optional[Batch] = None, group: Optional[Group] = None):
        self.batch = batch or pyglet.graphics.get_default_batch()
        self.group = AnchorGroup(window, window.width - 16, window.height - 30, 30, 30,
                                 anchor_y=Anchor.CENTER, anchor_x=Anchor.RIGHT,
                                 parent=group)

        self._window = window

        self.button = ToggleButton(0, 0, mute_image, unmute_image,
                                   batch=self.batch, group=self.group)

    def repack(self):
        self.group.x = self._window.width - 16
        self.group.y = self._window.height - 30


class GameWidgetBase(pyglet.event.EventDispatcher):
    S = TypeVar("S", bound=pyglet.shapes.ShapeBase)

    group: Union[Group, AnchorGroup]
    background: S

    def _check_hit(self, x, y):
        parent = self.group
        while parent is not None:
            if isinstance(parent, AnchorGroup):
                parent: AnchorGroup
                x, y = parent.transform_point(x, y)
                break
            else:
                parent = parent.parent

        return all((self.background.x < x < self.background.x + self.background.width,
                    self.background.y < y < self.background.y + self.background.height))


class LabeledTickBox(GameWidgetBase):
    height = 23

    def __init__(self, x, y, text, window, batch: Optional[Batch] = None, group: Optional[Group] = None):
        super().__init__()

        self.batch = batch or pyglet.graphics.get_default_batch()
        self.group = group or pyglet.graphics.get_default_group()

        self._window = window

        # Shadow showing the hovered option.
        self.background = Rectangle(x, y, 0, self.height,
                                    color=Colour.DIFFICULTY_SELECTED,
                                    batch=self.batch, group=Group(0, parent=self.group))
        self.background.visible = False

        self.checkbox = Sprite(checkmark_image, x=x, y=y,
                               batch=self.batch, group=Group(1, parent=self.group))
        self.checkbox.visible = False

        self.label = Label(text=text, font_name="Roboto Medium", font_size=12, bold=True,
                           color=Colour.DIFFICULTY_LABEL,
                           x=x + self.checkbox.width + 3, y=y + math.ceil(self.height / 2), anchor_y="center",
                           batch=self.batch, group=Group(1, parent=self.group))

    def on_mouse_motion(self, x, y, dx, dy):
        if self._check_hit(x, y) and self.group.parent.visible:
            if self.checkbox.visible:
                self._window.set_mouse_cursor()
            else:
                cursor = self._window.get_system_mouse_cursor(Window.CURSOR_HAND)
                self._window.set_mouse_cursor(cursor)

                self.background.visible = True
        else:
            self.background.visible = False

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        if self._check_hit(x, y) and self.group.parent.visible:
            self.background.visible = True
            return pyglet.event.EVENT_HANDLED
        else:
            self.background.visible = False

    def on_mouse_press(self, x, y, button, modifiers):
        if self._check_hit(x, y) and self.group.parent.visible:
            self.background.visible = True
            return pyglet.event.EVENT_HANDLED
        else:
            self.background.visible = False

    def on_mouse_release(self, x, y, button, modifiers):
        if self._check_hit(x, y) and self.group.parent.visible:
            self.dispatch_event("on_select", self)

            return pyglet.event.EVENT_HANDLED


LabeledTickBox.register_event_type("on_select")


class DifficultiesDropdown(GameWidgetBase):
    def __init__(self, window, difficulty: Difficulty, batch: Optional[Batch] = None, group: Optional[Group] = None):
        super().__init__()

        self.batch = batch or pyglet.graphics.get_default_batch()

        self.group = AnchorGroup(window, 15, window.height - 45, 0, 0,
                                 anchor_y=Anchor.TOP, anchor_x=Anchor.LEFT,
                                 order=1, parent=group)
        self.group.visible = False

        self._window = window

        cumulative_y = 5
        self.children = []
        for child_difficulty in reversed(Difficulty):
            child = LabeledTickBox(0, cumulative_y, child_difficulty, window,
                                   batch=self.batch, group=Group(1, parent=self.group))
            child.push_handlers(self)
            if child_difficulty == difficulty:
                child.checkbox.visible = True

            self.children.insert(0, child)
            cumulative_y += child.height
        cumulative_y += 5

        widest_child = max(self.children, key=lambda c: c.label.x + c.label.content_width)
        max_width = widest_child.label.x + widest_child.label.content_width + 28
        for child in self.children:
            child.background.width = max_width

        self.group.width = max_width
        self.group.height = cumulative_y

        self.background = shapes.RoundedRectangle(0, 0, max_width, cumulative_y, radius=8,
                                                  batch=self.batch,
                                                  group=Group(0, parent=self.group))

    def repack(self):
        self.group.y = self._window.height - 45

    def on_mouse_motion(self, x, y, dx, dy):
        if self._check_hit(x, y) and self.group.visible:
            return pyglet.event.EVENT_HANDLED

    def on_mouse_press(self, x, y, button, modifiers):
        if self._check_hit(x, y) and self.group.visible:
            return pyglet.event.EVENT_HANDLED

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        if self._check_hit(x, y) and self.group.visible:
            return pyglet.event.EVENT_HANDLED

    def on_select(self, widget):
        self.group.visible = False

        for child in self.children:
            child.checkbox.visible = False

        widget.checkbox.visible = True


class SelectedDifficultyButton(GameWidgetBase):
    def __init__(self, window, difficulty: Difficulty, batch: Optional[Batch] = None, group: Optional[Group] = None):
        super().__init__()

        self.batch = batch or pyglet.graphics.get_default_batch()
        self.group = AnchorGroup(window, 16, 30, 100, 30,
                                 anchor_x=Anchor.LEFT, anchor_y=Anchor.CENTER,
                                 parent=group)

        self._window = window

        cumulative_x = 6
        self.label = Label(difficulty,
                           font_name="Roboto Black", font_size=12, bold=True,
                           color=Colour.DIFFICULTY_LABEL,
                           x=6, y=15, anchor_y="center",
                           batch=self.batch, group=Group(1, parent=self.group))
        cumulative_x += 3 + self.label.content_width

        self.triangle = Triangle(0, 0, 8, 0, 4, -4, color=Colour.DIFFICULTY_LABEL,
                                 batch=self.batch, group=AnchorGroup(window, cumulative_x + 3, 30 - 14, 8, 4,
                                                                     anchor_x=Anchor.LEFT, anchor_y=Anchor.BOTTOM,
                                                                     order=1, parent=self.group))
        cumulative_x += 3 + 8

        self.background = shapes.RoundedRectangle(0, 0, cumulative_x + 5, 30, radius=5,
                                                  batch=self.batch,
                                                  group=Group(0, parent=self.group))

    @property
    def text(self) -> str:
        return self.label.text

    @text.setter
    def text(self, value):
        self.label.text = value
        self.repack()

    def repack(self):
        cumulative_x = 6
        cumulative_x += 3 + self.label.content_width

        self.triangle.group.x = cumulative_x + 3
        cumulative_x += 3 + 8
        self.background.width = cumulative_x + 5

    def on_mouse_motion(self, x, y, dx, dy):
        if self._check_hit(x, y):
            cursor = self._window.get_system_mouse_cursor(Window.CURSOR_HAND)
            self._window.set_mouse_cursor(cursor)
            return

        self._window.set_mouse_cursor()

    def on_mouse_press(self, x, y, button, modifiers):
        if self._check_hit(x, y):
            self.dispatch_event("on_dropdown")


SelectedDifficultyButton.register_event_type("on_dropdown")


class DifficultyMenu:
    def __init__(self, window, difficulty: Difficulty, batch: Optional[Batch] = None, group: Optional[Group] = None):
        super().__init__()

        self.batch = batch or pyglet.graphics.get_default_batch()
        self.group = AnchorGroup(window, 0, window.height,
                                 100, 60,
                                 anchor_y=Anchor.TOP, anchor_x=Anchor.LEFT, parent=group)
        self._window = window

        self.button = SelectedDifficultyButton(window, difficulty, batch=self.batch, group=self.group)
        self.button.push_handlers(self)  # Handle events from the button.

        self.dropdown = DifficultiesDropdown(window, difficulty, batch=self.batch, group=group)

        for child in self.dropdown.children:
            child.push_handlers(self)  # Handle selecting a difficulty.

    def repack(self):
        self.group.y = self._window.height

        self.dropdown.repack()

    def on_dropdown(self):
        self.dropdown.group.visible = not self.dropdown.group.visible

    def on_select(self, widget: LabeledTickBox):
        self.button.text = widget.label.text
