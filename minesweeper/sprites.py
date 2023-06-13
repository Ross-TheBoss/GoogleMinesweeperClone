import pyglet
from pyglet.gl import GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA, GL_TRIANGLES, glActiveTexture, GL_TEXTURE0, glBindTexture, \
    glEnable, GL_BLEND, glBlendFunc, glDisable
from pyglet.graphics.shader import ShaderProgram
from pyglet.sprite import Sprite

FULL_TEXTURE_COORDS = (0.0, 0.0, 0.0,
                       1.0, 0.0, 0.0,
                       1.0, 1.0, 0.0,
                       0.0, 1.0, 0.0)


# From: https://github.com/pyglet/pyglet/blob/master/examples/sprite/multi_texture_sprite.py
class MultiTextureSpriteGroup(pyglet.sprite.SpriteGroup):
    """A sprite group that uses multiple active textures.
    """

    def __init__(self, textures: dict, blend_src: int, blend_dest: int, program=None, parent=None):
        """Create a sprite group for multiple textures and samplers.
           All textures must share the same target type.

        :Parameters:
            `textures` : `dict`
                Textures in samplername : texture.
            `blend_src` : int
                OpenGL blend source mode; for example,
                ``GL_SRC_ALPHA``.
            `blend_dest` : int
                OpenGL blend destination mode; for example,
                ``GL_ONE_MINUS_SRC_ALPHA``.
            `parent` : `~pyglet.graphics.Group`
                Optional parent group.
        """
        self.textures = textures
        texture = list(self.textures.values())[0]
        self.target = texture.target
        super().__init__(texture, blend_src, blend_dest, program, parent)

    def set_state(self):
        self.program.use()

        for idx, name in enumerate(self.textures):
            self.program[name] = idx

        for i, texture in enumerate(self.textures.values()):
            glActiveTexture(GL_TEXTURE0 + i)
            glBindTexture(self.target, texture.id)

        glEnable(GL_BLEND)
        glBlendFunc(self.blend_src, self.blend_dest)

    def unset_state(self):
        glDisable(GL_BLEND)
        self.program.stop()
        glActiveTexture(GL_TEXTURE0)

    def __repr__(self):
        return f'{self.__class__.__name__}({self.texture}-{self.texture.id})'

    def __eq__(self, other):
        return (other.__class__ is self.__class__ and
                self.program is other.program and
                self.textures == other.textures and
                self.blend_src == other.blend_src and
                self.blend_dest == other.blend_dest)

    def __hash__(self):
        return hash((id(self.parent),
                     id(self.textures),
                     self.blend_src, self.blend_dest))


class MinefieldSprite(Sprite):
    group_class = MultiTextureSpriteGroup

    # noinspection PyMissingConstructor
    def __init__(self,
                 foreground_img, background_img,
                 tile_size: int,
                 x=0, y=0, z=0,
                 blend_src=GL_SRC_ALPHA,
                 blend_dest=GL_ONE_MINUS_SRC_ALPHA,
                 batch=None,
                 group=None,
                 subpixel=False):
        # Ensure the images are textures.
        textures = {
            "background_texture": background_img,
            "foreground_texture": foreground_img
        }

        same_target = all([texture.target for texture in textures.values()])
        assert same_target is True, "All textures need to be the same target."
        self._x = x
        self._y = y
        self._z = z
        self._program = ShaderProgram(pyglet.resource.shader("minefield.vert"),
                                      pyglet.resource.shader("minefield.frag"))

        # Use first image as base.
        self._textures = list(textures.values())
        self._texture = self._textures[0]

        self._batch = batch or pyglet.graphics.get_default_batch()
        self._group = self.group_class(textures, blend_src, blend_dest, self._program, group)
        self._subpixel = subpixel
        self._create_vertex_list()

        self._program["texture_dimensions"] = self._texture.width, self._texture.height
        self._program["tile_size"] = tile_size

    @property
    def images(self):
        return self._textures

    @property
    def program(self):
        return self._program

    @program.setter
    def program(self, program):
        if self._program == program:
            return
        self._group = self.group_class(self._texture,
                                       self._group.blend_src,
                                       self._group.blend_dest,
                                       program,
                                       self._group)
        self._batch.migrate(self._vertex_list, GL_TRIANGLES, self._group, self._batch)
        self._program = program


class CheckerboardSprite(Sprite):
    def __init__(self,
                 img,
                 tile_size: int,
                 color1: tuple[int, int, int, int], color2: tuple[int, int, int, int],
                 outline_color: tuple[int, int, int, int] = (0, 0, 0, 0),
                 outline_thickness=0.0,
                 x=0, y=0, z=0,
                 blend_src=GL_SRC_ALPHA,
                 blend_dest=GL_ONE_MINUS_SRC_ALPHA,
                 batch=None,
                 group=None,
                 subpixel=False):
        self._program = ShaderProgram(pyglet.resource.shader("outlined_checkerboard.vert"),
                                      pyglet.resource.shader("outlined_checkerboard.frag"))

        super().__init__(img, x=x, y=y, z=z,
                         blend_src=blend_src,
                         blend_dest=blend_dest,
                         batch=batch,
                         group=group,
                         subpixel=subpixel)

        assert tuple(self._vertex_list.tex_coords[:]) == FULL_TEXTURE_COORDS, \
            "A full texture must be used with this shader."

        self._program["color1"] = pyglet.math.Vec4(*color1) / 255
        self._program["color2"] = pyglet.math.Vec4(*color2) / 255
        self._program["texture_dimensions"] = self._texture.width, self._texture.height
        self._program["tile_size"] = tile_size
        self._program["outline_color"] = pyglet.math.Vec4(*outline_color) / 255
        self._program["outline_thickness"] = outline_thickness

    @property
    def program(self):
        return self._program

    @program.setter
    def program(self, program):
        if self._program == program:
            return
        self._group = self.group_class(self._texture,
                                       self._group.blend_src,
                                       self._group.blend_dest,
                                       program,
                                       self._group)
        self._batch.migrate(self._vertex_list, GL_TRIANGLES, self._group, self._batch)
        self._program = program


class EndGraphicSprite(Sprite):
    def __init__(self,
                 img,
                 x=0, y=0, z=0,
                 blend_src=GL_SRC_ALPHA,
                 blend_dest=GL_ONE_MINUS_SRC_ALPHA,
                 batch=None,
                 group=None,
                 subpixel=False):
        self._program = ShaderProgram(pyglet.resource.shader("rounded_bottom.vert"),
                                      pyglet.resource.shader("rounded_bottom.frag"))

        super().__init__(img, x=x, y=y, z=z,
                         blend_src=blend_src,
                         blend_dest=blend_dest,
                         batch=batch,
                         group=group,
                         subpixel=subpixel)

        assert tuple(self._vertex_list.tex_coords[:]) == FULL_TEXTURE_COORDS, \
            "A full texture must be used with this shader."

        self._program["texture_dimensions"] = self._texture.width, self._texture.height

    @property
    def program(self):
        return self._program

    @program.setter
    def program(self, program):
        if self._program == program:
            return
        self._group = self.group_class(self._texture,
                                       self._group.blend_src,
                                       self._group.blend_dest,
                                       program,
                                       self._group)
        self._batch.migrate(self._vertex_list, GL_TRIANGLES, self._group, self._batch)
        self._program = program
