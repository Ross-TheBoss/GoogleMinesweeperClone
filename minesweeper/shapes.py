import math
import random

from pyglet.gl import GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA
from pyglet.graphics import Batch
from pyglet.shapes import ShapeBase, get_default_shader, Rectangle


class RoundedRectangle(ShapeBase):
    def __init__(self, x, y, width, height, radius=0, segments=None, color=(255, 255, 255, 255),
                 batch=None, group=None):
        """Create a rectangle or square with rounded corners.

        The rectangle's anchor point defaults to the (x, y) coordinates,
        which are at the bottom left.

        :Parameters:
            `x` : float
                The X coordinate of the rectangle.
            `y` : float
                The Y coordinate of the rectangle.
            `width` : float
                The width of the rectangle.
            `height` : float
                The height of the rectangle.
            `radius` : float
                The radius of the corners.
            `segments` : int
                You can optionally specify how many distinct line segments
                the corners should be made from. If not specified it will be
                automatically calculated using the formula:
                `max(14, int(radius / 1.25))`.
            `color` : (int, int, int, int)
                The RGB or RGBA color of the circle, specified as a
                tuple of 3 or 4 ints in the range of 0-255. RGB colors
                will be treated as having an opacity of 255.
            `batch` : `~pyglet.graphics.Batch`
                Optional batch to add the rectangle to.
            `group` : `~pyglet.graphics.Group`
                Optional parent group of the rectangle.
        """
        self._x = x
        self._y = y
        self._width = width
        self._height = height
        self._rotation = 0
        self._radius = radius
        self._segments = segments or max(14, int(self._radius / 1.25))
        self._num_verts = 4 * (self._segments * 3) + 3 * 6

        r, g, b, *a = color
        self._rgba = r, g, b, a[0] if a else 255

        program = get_default_shader()
        self._batch = batch or Batch()
        self._group = self.group_class(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA, program, group)

        self._create_vertex_list()
        self._update_vertices()

    def _create_vertex_list(self):
        self._vertex_list = self._group.program.vertex_list(
            self._num_verts, self._draw_mode, self._batch, self._group,
            colors=('Bn', self._rgba * self._num_verts),
            translation=('f', (self._x, self._y) * self._num_verts)
        )

    def _update_vertices(self):
        if not self._visible:
            self._vertex_list.position[:] = (0, 0) * self._num_verts
        else:
            left = self._x
            right = self._x + self._width
            bottom = self._y
            top = self._y + self._height

            vertices = self._generate_rectangle(left,
                                                bottom + self._radius,
                                                self._width,
                                                self._height - self._radius * 2)

            vertices += self._generate_rectangle(left + self._radius,
                                                 bottom,
                                                 self._width - self._radius * 2,
                                                 self._radius)

            vertices += self._generate_rectangle(left + self._radius,
                                                 top - self._radius,
                                                 self._width - self._radius * 2,
                                                 self._radius)

            vertices += self._generate_sector(left + self._radius,
                                              bottom + self._radius,
                                              self._radius, self._segments,
                                              math.radians(90), math.radians(180))
            vertices += self._generate_sector(left + self._radius,
                                              top - self._radius,
                                              self._radius, self._segments,
                                              math.radians(90), math.radians(90))
            vertices += self._generate_sector(right - self._radius,
                                              top - self._radius,
                                              self._radius, self._segments,
                                              math.radians(90), math.radians(0))
            vertices += self._generate_sector(right - self._radius,
                                              bottom + self._radius,
                                              self._radius, self._segments,
                                              math.radians(90), math.radians(270))

            self._vertex_list.position[:] = tuple(
                value for vertex in vertices for value in vertex
            )

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

    @property
    def width(self):
        """The width of the rectangle.

        :type: float
        """
        return self._width

    @width.setter
    def width(self, value):
        self._width = value
        self._update_vertices()

    @property
    def height(self):
        return self._height

    @height.setter
    def height(self, value):
        """The height of the rectangle.

        :type: float
        """
        self._height = value
        self._update_vertices()

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
        self._vertex_list.rotation[:] = (rotation,) * self._num_verts


class TileParticle(Rectangle):
    def __init__(self, x, y, width, height, color=(255, 255, 255, 255), batch=None, group=None):
        super().__init__(x, y, width, height, color=color, batch=batch, group=group)

        self._unscaled_x = x
        self._unscaled_y = y
        self._unscaled_width = width
        self._unscaled_height = height

        self.scale = 1

        angle = random.randint(0, 180)
        magnitude = 1.3
        self._thrust_x = math.cos(math.radians(angle)) * magnitude
        self._thrust_y = math.sin(math.radians(angle)) * magnitude

        self.spin = random.random()

        self._velocity_x = 0
        self._velocity_y = 0

    def animate(self):
        self.scale = max(self.scale - 0.03, 0)

        gravity = 0.4
        decay = 0.7

        self._thrust_x *= decay
        self._thrust_y *= decay

        self._velocity_x += self._thrust_x
        self._velocity_y += self._thrust_y - gravity

        self._unscaled_x += self._velocity_x
        self._unscaled_y += self._velocity_y

        self._x = self._unscaled_x + (self._unscaled_width / 2) * (1 - self.scale)
        self._y = self._unscaled_y + (self._unscaled_height / 2) * (1 - self.scale)
        self._width = self._unscaled_width * self.scale
        self._height = self._unscaled_height * self.scale

        self.rotation += self.spin
        self._update_vertices()
        self._update_translation()
