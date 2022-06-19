import glooey
import pyglet
import os

from pyglet import font

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


class StaticImage(glooey.Image):
    def __init__(self, image=None, responsive=False):
        if responsive:
            self.custom_alignment = 'fill'
        glooey.Widget.__init__(self)
        self._image = image or self.custom_image
        self._responsive = responsive
        self._sprite = None

    def do_claim(self):
        if self.image is not None and not self._responsive:
            return self.image.width, self.image.height
        else:
            return 0, 0

    def do_regroup(self):
        if self._sprite is not None:
            self._sprite.batch = self.batch
            self._sprite.group = self.group

    def do_draw(self):
        if self.image is None:
            self.do_undraw()
            return

        if self._sprite is None:
            self._sprite = pyglet.sprite.Sprite(
                self.image, batch=self.batch, group=self.group)
        else:
            self._sprite.image = self.image

        self._sprite.x = self.rect.left
        self._sprite.y = self.rect.bottom

        if self._responsive:
            scale_x = self.rect.width / self.image.width
            scale_y = self.rect.height / self.image.height
            scale = min(scale_x, scale_y)
            self._sprite.scale = scale

            self._sprite.x += (self.rect.width - self._sprite.width) / 2
            self._sprite.y += (self.rect.height - self._sprite.height) / 2

    def do_undraw(self):
        if self._sprite is not None:
            self._sprite.delete()
            self._sprite = None

    def get_image(self):
        return self._image

    def set_image(self, new_image):
        if self._image is not new_image:
            self._image = new_image
            self._repack()

    def del_image(self):
        self.set_image(None)

    def get_appearance(self):
        return {'image': self._image}

    def set_appearance(self, *, image=None):
        self.set_image(image)

    @property
    def is_empty(self):
        return self._image is None


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
    custom_color = (74, 117, 44)


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

    print("Flag icon:", flag_icon.get_padded_rect())
    print("Flag counter:", flag_counter.get_padded_rect())

    print("Clock icon:", clock_icon.get_padded_rect())
    print("Clock counter:", clock_counter.get_padded_rect())

    pyglet.app.run()


if __name__ == "__main__":
    main()
