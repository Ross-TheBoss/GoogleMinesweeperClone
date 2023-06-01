import math
from typing import Any

import glooey
import pyglet
from autoprop import autoprop
from pyglet import gl


class TransparencyGroup(pyglet.graphics.Group):
    def set_state(self):
        pyglet.gl.glPushAttrib(pyglet.gl.GL_COLOR_BUFFER_BIT)
        pyglet.gl.glEnable(pyglet.gl.GL_BLEND)
        pyglet.gl.glBlendFunc(pyglet.gl.GL_SRC_ALPHA, pyglet.gl.GL_ONE_MINUS_SRC_ALPHA)

    def unset_state(self):
        pyglet.gl.glDisable(pyglet.gl.GL_BLEND)
        pyglet.gl.glPopAttrib()


@autoprop
class BorderedRectangle(glooey.drawing.Artist):
    def __init__(self, rect=None, radius=0, segments=None, color: Any = 'green', *,
                 batch=None, group=None, usage='static', hidden=False):

        self._rect = rect or glooey.Rect.null()
        self._radius = radius
        self._segments = segments or max(14, int(self._radius / 1.25))
        self._num_verts = 4 * (self._segments * 3) + 3 * 6

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
                                                 self._radius)

            vertices += self._generate_rectangle(self._rect.left + self._radius,
                                                 self._rect.top - self._radius,
                                                 self._rect.width - self._radius * 2,
                                                 self._radius)

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

    def set_appearance(self, *, color=None, radius=None, segments=None):
        self._radius = radius
        self._segments = segments
        self.update_rect()

        self.set_color(color)

    def _group_factory(self, parent):
        return TransparencyGroup(parent=parent)


@autoprop
class Triangle(glooey.drawing.Artist):
    def __init__(self, x, y, x1, y1, x2, y2, color: Any = 'green', *,
                 batch=None, group=None, usage='static', hidden=False):
        self._rect = glooey.Rect.null()

        self._x = x
        self._y = y
        self._x1 = x1
        self._y1 = y1
        self._x2 = x2
        self._y2 = y2

        self._rect.left = min(self._x, self._x1, self._x2)
        self._rect.width = max(self._x, self._x1, self._x2) - self._rect.left
        self._rect.bottom = min(self._y, self._y1, self._y2)
        self._rect.height = max(self._y, self._y1, self._y2) - self._rect.bottom

        self._color = glooey.drawing.Color.from_anything(color)

        data = 'v2f/' + usage, 'c4B/' + usage
        super().__init__(batch, group, 3, gl.GL_TRIANGLES, data, hidden)

        self.update_vertices()

    def get_x(self):
        return self._x

    def get_x1(self):
        return self._x1

    def get_x2(self):
        return self._x2

    def get_y(self):
        return self._y

    def get_y1(self):
        return self._y1

    def get_y2(self):
        return self._y2

    def get_rect(self):
        return self._rect

    def set_rect(self, new_rect):
        # Reposition
        dx = new_rect.left - self._rect.left
        dy = new_rect.bottom - self._rect.bottom

        self._x += dx
        self._x1 += dx
        self._x2 += dx

        self._y += dy
        self._y1 += dy
        self._y2 += dy

        self._rect = new_rect

        self.update_vertices()

    def update_vertices(self):
        if self.vertex_list:
            self.vertex_list.vertices = (self._x, self._y,
                                         self._x1, self._y1,
                                         self._x2, self._y2)

    def get_color(self):
        return self._color

    def set_color(self, new_color):
        self._color = new_color
        self.update_color()

    def update_color(self):
        if self.vertex_list:
            self.vertex_list.colors = 3 * self._color.tuple

    def _update_vertex_list(self):
        self.update_vertices()
        self.update_color()

    def set_appearance(self, *, color='green'):
        self.set_color(color)
