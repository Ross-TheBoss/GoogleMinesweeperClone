from typing import Optional

import pyglet
import os
import functools
import weakref

# Specify resource paths.
from pyglet.gl import GL_ONE_MINUS_SRC_ALPHA, GL_SRC_ALPHA

BASEDIR = os.path.dirname(os.path.abspath(__file__))

pyglet.resource.path = [os.path.join(BASEDIR, "assets"),
                        os.path.join(BASEDIR, "assets", "numbers"),
                        os.path.join(BASEDIR, "assets", "fonts", "Roboto")]
pyglet.resource.reindex()

# Default DPI = 96.
DPI = 96


# 96px = 1in
# 72pt = 1in

def convert_to_px(value, axis=0, parent: 'Positioner' = None):
    if value.endswith("px"):
        return float(value[:-2])
    elif value.endswith("pt"):
        return (DPI / 72) * float(value[:-2])
    elif value.endswith("pc"):
        return (DPI / 6) * float(value[:-2])
    elif value.endswith("cm"):
        return (DPI / 2.54) * float(value[:-2])
    elif value.endswith("mm"):
        return (DPI / 25.4) * float(value[:-2])
    elif value.endswith("Q"):
        return (DPI / 101.6) * float(value[:-1])
    elif value.endswith("in"):
        return DPI * float(value[:-2])
    elif value.endswith("%"):
        # Convert relative to parent.
        if axis == 0:
            # X-axis
            return parent.width * (float(value[:-1]) / 100)
        elif axis == 1:
            # Y-axis
            return parent.height * (float(value[:-1]) / 100)


# Frozen object - immutable.
class Positioner:
    def __init__(self, width: Optional[str] = None, height: Optional[str] = None,
                 x: str = "0px", y: str = "0px",
                 parent_anchor = None, parent: 'Positioner' = None) -> None:
        self._x = x
        self._y = y
        self._width = width
        self._height = height
        # Remove children from the set when they are deleted.
        self.children = weakref.WeakSet()

        self._x_converter = functools.partial(convert_to_px, axis=0, parent=parent)
        self._y_converter = functools.partial(convert_to_px, axis=1, parent=parent)
        self._width_converter = functools.partial(self.get_dimension, axis=0)
        self._height_converter = functools.partial(self.get_dimension, axis=1)

        if parent_anchor is None:
            # Where the rectangle is positioned relative to the parent.
            self.parent_anchor = ("bottom", "left")
        else:
            if parent_anchor[0] not in ("bottom", "center", "top"):
                raise ValueError("Invalid parent anchor y")
            elif parent_anchor[1] not in ("left", "center", "right"):
                raise ValueError("Invalid parent anchor x")

            self.parent_anchor = parent_anchor

        self.parent = parent

        if self.parent is not None:
            self.parent.children.add(self)

    def __str__(self):
        return f"Positioner(x={self.x}, y={self.y}, width={self.width}, height={self.height})"

    def get_dimension(self, value, axis: int):
        if value is None:
            # Calculate based upon children.
            if axis == 0:
                return sum(map(lambda c: c.width, self.children))
            elif axis == 1:
                return sum(map(lambda c: c.height, self.children))
        else:
            return convert_to_px(value, axis, parent=self.parent)

    def get_converter(self, n, axis=0):
        if n.endswith("px"):
            return lambda x: float(x[:-2])
        elif n.endswith("pt"):
            return lambda x: (DPI / 72) * float(x[:-2])
        elif n.endswith("pc"):
            return lambda x: (DPI / 6) * float(x[:-2])
        elif n.endswith("cm"):
            return lambda x: (DPI / 2.54) * float(x[:-2])
        elif n.endswith("mm"):
            return lambda x: (DPI / 25.4) * float(x[:-2])
        elif n.endswith("Q"):
            return lambda x: (DPI / 101.6) * float(x[:-1])
        elif n.endswith("in"):
            return lambda x: DPI * float(x[:-2])
        elif n.endswith("%"):
            # Convert relative to parent - not allowed if width and height of parent are None.
            # X-axis
            if axis == 0:
                return self.width_percentage_to_pt
            elif axis == 1:
                return self.height_percentage_to_pt

    def width_percentage_to_pt(self, percentage) -> float:
        return self.parent.width * (float(percentage[:-1]) / 100)

    def height_percentage_to_pt(self, percentage) -> float:
        return self.parent.height * (float(percentage[:-1]) / 100)

    def move(self, x: str, y: str) -> 'Positioner':
        return self.__class__(self._width, self._height,
                              f"{self.x+convert_to_px(x, axis=0, parent=self.parent)}px",
                              f"{self.y+convert_to_px(y, axis=1, parent=self.parent)}px",
                              parent=self.parent,
                              parent_anchor=self.parent_anchor)

    @property
    def child_dependent(self):
        return (self.parent._width is None) or (self.parent._height is None)

    @property
    def parent_dependent(self):
        return any(map(lambda s: s.endswith("%") if isinstance(s, str) else False,
                       (self._x, self._y, self._width, self._height)))

    @property
    def x(self) -> float:
        if self.parent is None:
            return self._x_converter(self._x)
        else:
            anchor_x = 0
            if self.parent_anchor is not None:
                if self.parent_anchor[1] == "left":
                    anchor_x = 0
                elif self.parent_anchor[1] == "center":
                    anchor_x = self.parent.width // 2
                elif self.parent_anchor[1] == "right":
                    anchor_x = self.parent.width

            return self.parent.x + anchor_x + self._x_converter(self._x)

    @property
    def rel_x(self) -> float:
        """
        The X coordinate relative to its parent.
        """
        return self._x_converter(self._x)

    @property
    def y(self) -> float:
        if self.parent is None:
            return self._y_converter(self._y)
        else:
            anchor_y = 0
            if self.parent_anchor is not None:
                if self.parent_anchor[0] == "bottom":
                    anchor_y = 0
                elif self.parent_anchor[0] == "center":
                    anchor_y = self.parent.height // 2
                elif self.parent_anchor[0] == "top":
                    anchor_y = self.parent.height

            return self.parent.y + anchor_y + self._y_converter(self._y)

    @property
    def rel_y(self) -> float:
        """
        The Y coordinate relative to its parent.
        """
        return self._y_converter(self._y)

    @property
    def width(self) -> float:
        return self._width_converter(self._width)

    @property
    def height(self) -> float:
        return self._height_converter(self._height)

    @property
    def right(self) -> float:
        return self.x + self.width

    @property
    def rel_right(self) -> float:
        return self.rel_x + self.width

    @property
    def top(self) -> float:
        return self.y + self.height

    @property
    def rel_top(self) -> float:
        return self.rel_y + self.height


def main():
    width = 600
    height = 600

    win = pyglet.window.Window(width=600, height=560)
    batch = pyglet.graphics.Batch()

    img = pyglet.resource.image("clock_icon.png")

    win_positioner = Positioner(f"{width}px", f"{height}px")

    header = Positioner("100%", "60px", y="-60px",
                        parent=win_positioner,
                        parent_anchor=("center", "center"))
    print(header.x, header.y, header.width, header.height)

    @win.event
    def on_draw():
        win.clear()
        batch.draw()

    pyglet.app.run()


if __name__ == "__main__":
    main()
