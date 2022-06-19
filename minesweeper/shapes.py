"""
Additional 2D shapes needed for the minesweeper GUI.
"""

import math

from pyglet import gl
from pyglet.graphics import Batch
from pyglet.shapes import Triangle, _rotate, _ShapeGroup, _ShapeBase


class RoundedRectangle(_ShapeBase):
    def __init__(self, x, y, width, height, radius, segments=None, color=(255, 255, 255),
                 batch=None, group=None):

        self._x = x
        self._y = y
        self._width = width
        self._height = height
        self._radius = min(self._width//2, self._height//2, radius)
        self._segments = segments or max(14, int(self._radius / 1.25))
        self._num_verts = 4 * (self._segments * 3) + 2 * 6

        self._rotation = 0
        self._rgb = color

        self._batch = batch or Batch()
        self._group = _ShapeGroup(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA, group)
        self._vertex_list = self._batch.add(self._num_verts, gl.GL_TRIANGLES,
                                            self._group, "v2f", "c4B")
        self._update_position()
        self._update_color()

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

    def _update_position(self):
        if not self._visible:
            self._vertex_list.vertices = (0,) * (self._num_verts * 2)
        else:
            x1 = self._x - self._anchor_x
            y1 = self._y - self._anchor_y

            vertices = self._generate_rectangle(x1, y1 + self._radius,
                                                self.width,
                                                self.height - self._radius * 2)
            vertices += self._generate_rectangle(x1 + self._radius, y1,
                                                 self.width - self._radius * 2,
                                                 self.height)

            vertices += self._generate_sector(x1 + self._radius,
                                              y1 + self._radius,
                                              self._radius, self._segments,
                                              math.radians(90), math.radians(180))
            vertices += self._generate_sector(x1 + self._radius,
                                              y1 + self._height - self._radius,
                                              self._radius, self._segments,
                                              math.radians(90), math.radians(90))
            vertices += self._generate_sector(x1 + self._width - self._radius,
                                              y1 + self._height - self._radius,
                                              self._radius, self._segments,
                                              math.radians(90), math.radians(0))
            vertices += self._generate_sector(x1 + self._width - self._radius,
                                              y1 + self._radius,
                                              self._radius, self._segments,
                                              math.radians(90), math.radians(270))

            if self._rotation:
                vertices = _rotate(vertices, self._rotation, self.x, self.y)

            self._vertex_list.vertices = tuple(value for vertex in vertices for value in vertex)

    def _update_color(self):
        self._vertex_list.colors[:] = [*self._rgb, int(self._opacity)] * self._num_verts

    @property
    def width(self):
        """The width of the rectangle.
        :type: float
        """
        return self._width

    @width.setter
    def width(self, value):
        self._width = value
        self._update_position()

    @property
    def height(self):
        """The height of the rectangle.
        :type: float
        """
        return self._height

    @height.setter
    def height(self, value):
        self._height = value
        self._update_position()

    @property
    def rotation(self):
        """Clockwise rotation of the rectangle, in degrees.
        The Rectangle will be rotated about its (anchor_x, anchor_y)
        position.
        :type: float
        """
        return self._rotation

    @rotation.setter
    def rotation(self, rotation):
        self._rotation = rotation
        self._update_position()


def generate_dropdown_arrow(x, y, batch=None, group=None):
    return Triangle(x, y, x + 8, y, x + 4, y - 4,
                    batch=batch, group=group, color=(0, 0, 0))