from enum import Enum
from typing import Optional

import glooey
import pyglet
import os

from autoprop import autoprop
from pyglet import font
from pyglet import gl
from pyglet.window import Window

from minesweeper.artists import BorderedRectangle, Triangle


class Colour(tuple, Enum):
    _hint = tuple[int, int, int]

    WHITE: _hint = (255, 255, 255)
    HEADER_GREEN: _hint = (74, 117, 44)
    DIFFICULTY_SELECTED: _hint = (229, 229, 229)
    DIFFICULTY_LABEL: _hint = (48, 48, 48)


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


class RoundedRectangleWidget(glooey.Widget):
    custom_radius = None
    custom_color = 'green'
    custom_segments = None

    def __init__(self, **kwargs):
        super().__init__()
        self.artist = BorderedRectangle(
            radius=kwargs.get("radius", self.custom_radius),
            color=kwargs.get("color", self.custom_color),
            segments=kwargs.get("segments", self.custom_segments),
            hidden=True
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
        return False

    def set_appearance(self, *, color=None, radius=None, segments=None):
        self.artist.set_appearance(
            color=color,
            radius=radius,
            segments=segments,
        )
        self._repack()


class TriangleWidget(glooey.Widget):
    custom_x = None
    custom_y = None
    custom_x1 = None
    custom_y1 = None
    custom_x2 = None
    custom_y2 = None

    custom_color = 'green'

    def __init__(self, **kwargs):
        super().__init__()
        self.artist = Triangle(
            x=kwargs.get("x", self.custom_x),
            y=kwargs.get("y", self.custom_y),
            x1=kwargs.get("x1", self.custom_x1),
            y1=kwargs.get("y1", self.custom_y1),
            x2=kwargs.get("x2", self.custom_x2),
            y2=kwargs.get("y2", self.custom_y2),
            color=kwargs.get("color", self.custom_color),
            hidden=True
        )

    def do_claim(self):
        return self.artist.get_rect().width, self.artist.get_rect().height

    def do_regroup(self):
        self.artist.batch = self.batch
        self.artist.group = self.group

    def do_resize(self):
        self.artist.rect = self.rect

    def do_draw(self):
        self.artist.show()

    def do_undraw(self):
        self.artist.hide()

    def set_appearance(self, *, color='green'):
        self.artist.set_appearance(
            color=color,
        )
        self._repack()


class HeaderLabel(glooey.Label):
    custom_font_name = "Roboto Medium"
    custom_font_size = 12
    custom_bold = True
    custom_color = Colour.DIFFICULTY_LABEL


@autoprop
class DropdownButtonLabel(glooey.Widget):
    custom_height_hint = 30

    class Label(HeaderLabel):
        custom_right_padding = 3
        custom_left_padding = 6

        custom_vert_padding = 6  # = (30 - 18) / 2

    label: Label

    class Arrow(TriangleWidget):
        custom_x = 0
        custom_y = 0
        custom_x1 = 8
        custom_y1 = 0
        custom_x2 = 4
        custom_y2 = -4

        custom_top_padding = 13
        custom_right_padding = 8
        custom_left_padding = 3
        custom_bottom_padding = 10

        custom_alignment = "top"
        custom_color = Colour.DIFFICULTY_LABEL

    arrow: Arrow

    class HBox(glooey.HBox):
        pass

    hbox: HBox

    def __init__(self, text):
        super().__init__()
        hbox = self.HBox()
        self.label = self.Label(text)
        self.arrow = self.Arrow()

        hbox.pack(self.label)
        hbox.add(self.arrow)

        self._attach_child(hbox)

    # Access attributes of label.
    def set_text(self, text, width=None, **style):
        self.label.set_text(text, width=width, **style)

    def get_text(self):
        return self.label.text


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


@autoprop
class StatisticWidget(glooey.Label):
    custom_left_padding = 3
    custom_top_padding = 2

    custom_font_name = "Roboto"
    custom_font_size = 15
    custom_bold = True
    custom_height_hint = 20

    custom_alignment = "left"

    custom_color = Colour.WHITE


class HeaderBackground(glooey.Background):
    custom_alignment = "fill top"
    custom_height_hint = 60
    custom_color = Colour.HEADER_GREEN


@autoprop
class SelectedDifficultyButton(glooey.Button):
    custom_left_padding = 16
    custom_top_padding = 15

    custom_alignment = "top left"
    custom_height_hint = 30

    Foreground = DropdownButtonLabel

    class Background(RoundedRectangleWidget):
        custom_height_hint = 30
        custom_radius = 5

        custom_color = Colour.WHITE

    # Access attributes of label.
    def set_text(self, text, width=None, **style):
        self._foreground.set_text(text, width=width, **style)

    def get_text(self):
        return self._foreground.text


@autoprop
class LabeledTickBox(glooey.Stack):
    class Background(glooey.Background):
        custom_color = Colour.DIFFICULTY_SELECTED

    shadow: Background

    class RadioButton(glooey.RadioButton):
        custom_checked_base = pyglet.resource.image("checkmark.png")
        custom_unchecked_base = pyglet.image.create(25, 21)

        def toggle(self, direct: bool = False):
            if self.is_enabled:
                if self.is_checked:
                    # The checkbox can only be un-checked if another box gets checked.
                    if not direct:
                        self._deck.state = False
                else:
                    self._deck.state = True

                self.dispatch_event('on_toggle', self)

        def on_click(self, widget):
            if self._defer_clicks_to_proxies and widget is self:
                return
            else:
                self.toggle(True)

    radio_button: RadioButton

    class Label(HeaderLabel):
        custom_left_padding = 3  # = 28 - (Radio Button width)
        custom_right_padding = 16

        def do_resize(self):
            # Do not show the label at the bottom left
            # when resizing the screen from the top of the window.
            if self.is_hidden:
                self._layout.delete()

        def do_claim(self):
            output = super().do_claim()
            if self.is_hidden:
                self.do_undraw()
            return output

    label: Label

    def __init__(self, text, peers: Optional[list] = None, is_checked: bool = False):
        super().__init__()

        hbox = glooey.HBox()
        self.radio_button = self.RadioButton(peers=peers, is_checked=is_checked)
        self.label = self.Label(text)
        self.shadow = self.Background()
        self.shadow.hide()

        hbox.pack(self.radio_button)
        hbox.add(self.label)

        # Configure `checkbox` to respond to clicks anywhere in `hbox`
        self.radio_button.add_proxy(hbox, exclusive=True)

        # Make the `on_toggle` events appear to come from this widget.
        self.relay_events_from(self.radio_button, "on_toggle")

        self.add(self.shadow)
        self.add(hbox)

    def toggle(self):
        self.radio_button.toggle()

    def check(self):
        self.radio_button.check()

    def uncheck(self):
        self.radio_button.uncheck()

    def on_mouse_enter(self, x, y):
        if self.shadow.is_hidden:
            self.shadow.unhide()

    def on_mouse_leave(self, x, y):
        if not self.shadow.is_hidden:
            self.shadow.hide()

    # Access attributes of radio_button.
    @property
    def is_checked(self):
        return self.radio_button.is_checked

    def get_peers(self):
        return self.radio_button.peers

    def set_peers(self, new_peers):
        self.radio_button.peers = new_peers

    # Access attributes of label.
    def get_text(self):
        return self.label.text

    def set_text(self, text, width=None, **style):
        self.label.set_text(text, width=width, **style)


@autoprop
@glooey.register_event_type("on_toggle", "on_selection")
class TickBoxVBox(glooey.VBox):
    def __init__(self, children: list[LabeledTickBox],
                 selected_index: int = 0,
                 default_cell_size=None):
        super().__init__(default_cell_size=default_cell_size)

        self.checkboxes = []
        for child in children:
            self.add(child)

        self._selected_index = selected_index
        self.children[self._selected_index].check()

    def on_toggle(self, widget: glooey.RadioButton):
        if widget.is_checked:
            self._selected_index = self.checkboxes.index(widget)
            self.dispatch_event("on_selection")

    def insert(self, widget, index, size=None):
        self.checkboxes.insert(index, widget.radio_button)
        widget.radio_button.peers = self.checkboxes

        self.relay_events_from(widget, "on_toggle")

        super().insert(widget, index, size)

    def remove(self, widget):
        self.checkboxes.remove(widget.radio_button)
        widget.peers = []

        super().remove(widget)

    def clear(self):
        self.checkboxes = []

        super().clear()

    def unhide(self, draw=True):
        super().unhide(draw)
        self.children[self._selected_index].shadow.unhide(draw)

    def get_selected_index(self):
        return self._selected_index

    def set_selected_index(self, new_selected_index):
        self._selected_index = new_selected_index
        self.children[self._selected_index].check()

    def get_selected_widget(self):
        return self.children[self.selected_index]


@autoprop
@glooey.register_event_type("on_selection")
class DifficultiesDropdown(glooey.Stack):
    custom_alignment = "top left"
    custom_left_padding = 16

    class Background(RoundedRectangleWidget):
        custom_radius = 8
        custom_color = Colour.WHITE

    background: Background

    class TickBoxVBox(TickBoxVBox):
        custom_cell_padding = -2  # Remove the default 1px border.

        custom_top_padding = 5
        custom_bottom_padding = 5

        custom_default_cell_size = 23
        custom_cell_alignment = "fill horz"

    vbox: TickBoxVBox

    def __init__(self, children: list[LabeledTickBox], selected_index=0):
        super().__init__()
        self.vbox = self.TickBoxVBox(children, selected_index=selected_index)
        self.background = self.Background()

        self.relay_events_from(self.vbox, "on_selection")

        self.add(self.background)
        self.add(self.vbox)

    # Access attributes of vbox.
    def get_selected_index(self):
        return self.vbox.selected_index

    def set_selected_index(self, new_selected_index):
        self.vbox.selected_index = new_selected_index

    def get_selected_widget(self):
        return self.vbox.get_selected_widget()


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

    # Difficulty menu
    diff_menu = glooey.VBox()
    gui.add(diff_menu)

    diff_label = SelectedDifficultyButton("Easy")
    diff_menu.pack(diff_label)

    boxes = [LabeledTickBox("Easy"),
             LabeledTickBox("Medium"),
             LabeledTickBox("Hard"),
             LabeledTickBox("Extreme"),
             LabeledTickBox("Lottery")]

    diff_dropdown = DifficultiesDropdown(boxes)
    diff_dropdown.hide()

    diff_menu.pack(diff_dropdown)

    @diff_label.event
    def on_mouse_enter(x, y):
        window.set_mouse_cursor(window.get_system_mouse_cursor(Window.CURSOR_HAND))

    @diff_label.event
    def on_mouse_leave(x, y):
        window.set_mouse_cursor(window.get_system_mouse_cursor(Window.CURSOR_DEFAULT))

    @diff_label.event
    def on_click(widget):
        if diff_dropdown.is_hidden:
            diff_dropdown.unhide()
        else:
            diff_dropdown.hide()

    @diff_dropdown.event
    def on_selection():
        diff_label.text = diff_dropdown.vbox.children[diff_dropdown.selected_index].text

    pyglet.app.run()


if __name__ == "__main__":
    main()
