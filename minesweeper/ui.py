import math
from typing import Any

import glooey
import pyglet
import os

from autoprop import autoprop
from pyglet import font, gl

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

@autoprop
class BorderedRectangle(glooey.drawing.Artist):
    def __init__(self, rect=None, radius=0, segments=None, color: Any = 'green', *,
                 batch=None, group=None, usage='static', hidden=False):

        self._rect = rect or glooey.Rect.null()
        self._radius = radius
        self._segments = segments or max(14, int(self._radius / 1.25))
        self._num_verts = 4 * (self._segments * 3) + 2 * 6

        print(radius)

        self._color = glooey.drawing.Color.from_anything(color)

        data = 'v2f/' + usage, 'c4B/' + usage
        super().__init__(batch, group, self._num_verts, gl.GL_TRIANGLES, data, hidden)

    @staticmethod
    def _generate_rectangle(x, y, width, height):
        return [(x, y),
                (x, y + height),
                (x + width, y + height),
                (x, y),
                (x + width, y + height),
                (x + width, y)]

    @staticmethod
    def _generate_sector(x, y, radius, segments=None, angle=math.tau, start_angle=0.):
        segments = segments or max(14, int(radius / 1.25))

        r = radius
        tau_segs = angle / segments

        # Calculate the outer points of the sector.
        points = [(x + (r * math.cos((i * tau_segs) + start_angle)),
                   y + (r * math.sin((i * tau_segs) + start_angle))) for i in
                  range(segments + 1)]

        # Create a list of triangles from the points
        vertices = []
        for i, point in enumerate(points[1:], start=1):
            vertices += [(x, y), points[i - 1], point]

        return vertices

    def get_rect(self):
        return self._rect

    def set_rect(self, new_rect):
        self._rect = new_rect
        self.update_rect()

    def update_rect(self):
        if self.vertex_list:
            vertices = self._generate_rectangle(self._rect.left,
                                                self._rect.bottom + self._radius,
                                                self._rect.width,
                                                self._rect.height - self._radius * 2)

            vertices += self._generate_rectangle(self._rect.left + self._radius,
                                                 self._rect.bottom,
                                                 self._rect.width - self._radius * 2,
                                                 self._rect.height)

            vertices += self._generate_sector(self._rect.left + self._radius,
                                              self._rect.bottom + self._radius,
                                              self._radius, self._segments,
                                              math.radians(90), math.radians(180))
            vertices += self._generate_sector(self._rect.left + self._radius,
                                              self._rect.top - self._radius,
                                              self._radius, self._segments,
                                              math.radians(90), math.radians(90))
            vertices += self._generate_sector(self._rect.right - self._radius,
                                              self._rect.top - self._radius,
                                              self._radius, self._segments,
                                              math.radians(90), math.radians(0))
            vertices += self._generate_sector(self._rect.right - self._radius,
                                              self._rect.bottom + self._radius,
                                              self._radius, self._segments,
                                              math.radians(90), math.radians(270))

            self.vertex_list.vertices = tuple(
                value for vertex in vertices for value in vertex)

    def get_color(self):
        return self._color

    def set_color(self, new_color):
        self._color = new_color
        self.update_color()

    def update_color(self):
        if self.vertex_list:
            self.vertex_list.colors = self._num_verts * self._color.tuple

    def _update_vertex_list(self):
        self.update_rect()
        self.update_color()

    def set_appearance(self, rect=None, color=None, radius=None, segments=None):
        self._radius = radius
        self._segments = segments

        self.set_rect(rect)
        self.set_color(color)


class ButtonBackground(glooey.Widget):
    custom_height_hint = 30

    def __init__(self):
        super().__init__()
        self.artist = BorderedRectangle(
            radius=5,
            color=(255, 255, 255),
            hidden=True,
        )

    def do_claim(self):
        return 0, 0

    def do_regroup(self):
        self.artist.batch = self.batch
        self.artist.group = self.group

    def do_resize(self):
        self.artist.rect = self.rect

    def do_draw(self):
        self.artist.show()

    def do_undraw(self):
        self.artist.hide()

    def is_empty(self):
        return self.artist.is_empty

    def set_appearance(self, *, rect=None, color=None, radius=None, segments=None):
        self.artist.set_appearance(
                rect=rect,
                color=color,
                radius=radius,
                segments=segments,
        )
        self._repack()


class HeaderCenter(glooey.HBox):
    def top_35(self, widget_rect, max_rect):
        widget_rect.width = 0.35 * max_rect.width
        widget_rect.height = min(self.get_height_hint(), max_rect.height)
        widget_rect.top_center = max_rect.top_center

    def do_resize(self):
        self.set_default_cell_size(self.get_width() // 5 + 3)
        super().do_resize()

    custom_height_hint = 60
    custom_alignment = top_35


class StatisticWidget(glooey.Label):
    custom_left_padding = 3
    custom_top_padding = 2

    custom_font_name = "Roboto"
    custom_font_size = 15
    custom_bold = True
    custom_height_hint = 20

    custom_alignment = "left"

    custom_color = (255, 255, 255)


class HeaderBackground(glooey.Background):
    custom_alignment = "fill top"
    custom_height_hint = 60
    custom_color = (74, 117, 44)  # Colour.HEADER_GREEN


class SelectedDifficultyButton(glooey.Button):
    custom_left_padding = 16
    custom_top_padding = 15

    custom_alignment = "top left"
    custom_height_hint = 30

    class Foreground(glooey.Label):
        custom_right_padding = 3
        custom_left_padding = 6

        custom_alignment = "center"

        custom_font_name = "Roboto Medium"
        custom_bold = True
        custom_color = (48, 48, 48)  # Colour.DIFFICULTY_LABEL

    class Background(ButtonBackground): pass


def main():
    window = pyglet.window.Window(450, 420, resizable=True)
    gui = glooey.Gui(window)
    header = HeaderBackground()
    gui.add(header)

    # counters are slightly more compressed & anti-aliased in the original.
    counters = HeaderCenter()
    gui.add(counters)

    flag_icon = glooey.Image(flag_image)
    flag_counter = StatisticWidget("10")
    clock_icon = glooey.Image(clock_image)
    clock_counter = StatisticWidget("000")

    counters.pack(flag_icon)
    counters.add(flag_counter)
    counters.pack(clock_icon)
    counters.add(clock_counter)

    diff_label = SelectedDifficultyButton("Easy")

    gui.add(diff_label)

    print("Flag icon:", flag_icon.get_padded_rect())
    print("Flag counter:", flag_counter.get_padded_rect())

    print("Clock icon:", clock_icon.get_padded_rect())
    print("Clock counter:", clock_counter.get_padded_rect())

    pyglet.app.run()


if __name__ == "__main__":
    main()
