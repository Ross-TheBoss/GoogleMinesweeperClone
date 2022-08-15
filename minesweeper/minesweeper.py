"""
A Google Minesweeper clone made using pyglet.
"""

import math
import random
import os.path

from collections import namedtuple
from enum import Enum
from queue import Queue
from typing import Optional

import glooey
import pyglet
from autoprop import autoprop

from pyglet import font
from pyglet.graphics import OrderedGroup, Group, Batch
from pyglet.image import SolidColorImagePattern
from pyglet.image import TextureRegion, Texture
from pyglet.sprite import Sprite
from pyglet.window import mouse, Window

import minesweeper.ui as ui


class Colour(tuple, Enum):
    _hint = tuple[int, int, int, int]

    def to_rgb(self):
        return self[0], self[1], self[2]

    LIGHT_GREEN: _hint = (170, 215, 81, 255)
    LIGHT_GREEN_HOVER: _hint = (191, 225, 125, 255)

    DARK_GREEN: _hint = (162, 209, 73, 255)
    DARK_GREEN_HOVER: _hint = (185, 221, 119, 255)

    HEADER_GREEN: _hint = (74, 117, 44, 255)

    LIGHT_BROWN: _hint = (229, 194, 159, 255)
    DARK_BROWN: _hint = (215, 184, 153, 255)

    DIFFICULTY_SELECTED: _hint = (229, 229, 229, 255)

    TRANSPARENT: _hint = (0, 0, 0, 0)
    ONE: _hint = (25, 118, 210, 255)
    TWO: _hint = (56, 142, 60, 255)
    THREE: _hint = (211, 47, 47, 255)
    FOUR: _hint = (123, 31, 162, 255)
    FIVE: _hint = (255, 143, 0, 255)
    SIX: _hint = (0, 151, 167, 255)
    SEVEN: _hint = (66, 66, 66, 255)
    EIGHT: _hint = (158, 158, 158, 255)

    DIFFICULTY_LABEL: _hint = (48, 48, 48, 255)


NUM_COLOURS = (Colour.TRANSPARENT,
               Colour.ONE,
               Colour.TWO,
               Colour.THREE,
               Colour.FOUR,
               Colour.FIVE,
               Colour.SIX,
               Colour.SEVEN,
               Colour.EIGHT)


class Ordinal(tuple, Enum):
    NORTH = (1, 0)
    NORTH_EAST = (1, -1)
    EAST = (0, -1)
    SOUTH_EAST = (-1, -1)
    SOUTH = (-1, 0)
    SOUTH_WEST = (-1, 1)
    WEST = (0, 1)
    NORTH_WEST = (1, 1)


class Difficulty(str, Enum):
    EASY = "Easy"
    MEDIUM = "Medium"
    HARD = "Hard"
    EXTREME = "Extreme"
    LOTTERY = "Lottery"


DifficultySettingsTuple = namedtuple("DifficultySettingsTuple",
                                     ["columns", "rows", "tile", "mines",
                                      "guaranteed_start"])

DIFFICULTY_SETTINGS = {
    Difficulty.EASY: DifficultySettingsTuple(10, 8, 45, 10, True),
    Difficulty.MEDIUM: DifficultySettingsTuple(18, 14, 30, 40, True),
    Difficulty.HARD: DifficultySettingsTuple(24, 20, 25, 99, True),
    Difficulty.EXTREME: DifficultySettingsTuple(38, 30, 20, 300, True),
    Difficulty.LOTTERY: DifficultySettingsTuple(5, 5, 100, 24, False)
}

# Specify resource paths.
BASEDIR = os.path.dirname(os.path.abspath(__file__))

pyglet.resource.path = [os.path.join(BASEDIR, "assets"),
                        os.path.join(BASEDIR, "assets", "numbers"),
                        os.path.join(BASEDIR, "assets", "sfx"),
                        os.path.join(BASEDIR, "assets", "fonts", "Roboto")]
pyglet.resource.reindex()

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

flag_image = pyglet.resource.image("flag_icon.png")
clock_image = pyglet.resource.image("clock_icon.png")

# Sound effects
clear_sfx = pyglet.resource.media("clear.mp3", streaming=False)
flood_sfx = pyglet.resource.media("flood.mp3", streaming=False)

flag_place_sfx = pyglet.resource.media("flag place.mp3", streaming=False)
flag_remove_sfx = pyglet.resource.media("flag remove.mp3", streaming=False)


def create_checkerboard_image(width, height,
                              tile_width, tile_height,
                              colour1: tuple[int, int, int, int],
                              colour2: tuple[int, int, int, int]) -> TextureRegion:
    """
    Create a checkerboard image with the specified width and height,
    containing tiles of the specified tile_width and tile_height.
    """

    # Create a blank background texture.
    bg = Texture.create(width, height)

    tile_img1 = SolidColorImagePattern(colour1) \
        .create_image(tile_width, tile_height)

    tile_img2 = SolidColorImagePattern(colour2) \
        .create_image(tile_width, tile_height)

    rows = math.ceil(width / tile_img1.width)
    columns = math.ceil(height / tile_img1.height)

    for y in range(columns):
        for x in range(rows):
            if x % 2 + y % 2 == 1:
                bg.blit_into(tile_img1,
                             x * tile_img1.width,
                             y * tile_img1.height, 0)
            else:
                bg.blit_into(tile_img2,
                             x * tile_img2.width,
                             y * tile_img2.height, 0)

    return bg


def create_grid(rows: int, columns: int, fill=None) -> list[list]:
    """
    Create a 2d list filled with fill.
    """
    return [[fill] * columns for _ in range(rows)]


class Minefield:
    MINE: int = 9

    def __init__(self, rows: int, columns: int):
        """Create a minefield.

        A minefield is a 2 dimensional list where each cell describes how
        many mines are around it, unless that cell is a mine itself.

        In that case it has a special value (which is Minefield.MINE).
        """
        self._grid: list[list[int]] = create_grid(rows, columns, 0)
        self._empty = True

        self.rows: int = rows
        self.columns: int = columns

    def __repr__(self):
        return f"{self.__class__.__name__}({self.rows}, {self.columns})"

    def __str__(self):
        return "\n".join(" ".join(map("{: >2}".format, row))
                         for row in self._grid)

    def __iter__(self):
        return iter(self._grid)

    def __getitem__(self, item):
        return self._grid.__getitem__(item)

    def __setitem__(self, item, value):
        return self._grid.__setitem__(item, value)

    @property
    def area(self):
        """Returns the area of the Minefield."""
        return self.rows * self.columns

    @property
    def density(self):
        """Returns the density of mines in the minefield."""
        return sum(row.count(Minefield.MINE) for row in self._grid) / self.area

    @property
    def empty(self):
        return self._empty

    def valid_index(self, row, column=0) -> bool:
        """Returns whether the specified row and column is a valid index."""
        return (0 <= row < self.rows) and (0 <= column < self.columns)

    def generate(self, n, clear_position: Optional[int] = None):
        """Place n mines randomly throughout the grid and make each value
         in the grid count the number of mines around it."""
        self.generate_mines(n, clear_position)
        self.generate_surroundings()

    def generate_mines(self, n, clear_position: Optional[int] = None) -> None:
        """Places n mines randomly throughout the grid where
        clear_position doesn't contain a mine. """
        self._empty = False

        n = min(n, self.columns * self.rows)

        # Ensure that clear position doesn't contain a mine.
        positions = random.sample(range(self.columns * self.rows), n)
        if clear_position is not None:
            tries = 1
            while clear_position in positions:
                tries += 1
                positions = random.sample(range(self.columns * self.rows), n)

        for pos in positions:
            self._grid[pos // self.columns][pos % self.columns] = Minefield.MINE

    def generate_surroundings(self) -> None:
        """Modifies the values within the grid to reflect the number of mines that surround them."""
        for row in range(self.rows):
            for column in range(self.columns):
                if self._grid[row][column] != 0:
                    continue

                # Scan around the tile, counting the surrounding mines.
                count = 0
                for dy, dx in Ordinal:
                    if self.valid_index(row + dy, column + dx):
                        count += self._grid[row + dy][column + dx] == Minefield.MINE

                self._grid[row][column] = count

    def minesweep(self, row, column, uncovered: Optional[list[list[bool]]] = None) -> \
    list[list[bool]]:
        """Returns which cells are uncovered by performing the flood fill algorithm
        starting at row and column. This is done using the breadth-first search algorithm.
        """
        if uncovered is None:
            uncovered: list[list[bool]] = create_grid(self.rows, self.columns, False)

        if not self.valid_index(row, column):
            return uncovered

        queue = Queue()
        queue.put((row, column))

        while not queue.empty():
            row, column = queue.get()
            if (not self.valid_index(row, column)) or uncovered[row][column]:
                continue
            elif self._grid[row][column] != 0:
                uncovered[row][column] = True
            else:
                uncovered[row][column] = True

                for dy, dx in Ordinal:
                    queue.put((row + dy, column + dx))

        return uncovered

    def recursive_minesweep(self, row, column,
                            uncovered: Optional[list[list[bool]]] = None) -> list[
        list[bool]]:
        """Returns which cells are uncovered by performing the flood fill algorithm,
        starting at row and column. This is done using the depth-first search algorithm.
        """
        if uncovered is None:
            uncovered: list[list[bool]] = create_grid(self.rows, self.columns, False)

        if (not self.valid_index(row, column)) or uncovered[row][column]:
            return uncovered
        elif self._grid[row][column] != 0:
            uncovered[row][column] = True
            return uncovered
        else:
            uncovered[row][column] = True

            for dy, dx in Ordinal:
                uncovered = self.recursive_minesweep(row + dy, column + dx, uncovered)

            return uncovered

    def minesweep_iter(self, row, column,
                       uncovered: Optional[list[list[bool]]] = None) -> iter:
        """Returns an iterator containing the index of which cells are uncovered by
        performing the flood fill algorithm, starting at row and column.
        """
        if not self.valid_index(row, column):
            return StopIteration

        if uncovered is None:
            uncovered: list[list[bool]] = create_grid(self.rows, self.columns, False)

        queue = Queue()
        queue.put((row, column))
        while not queue.empty():
            row, column = queue.get()
            if (not self.valid_index(row, column)) or uncovered[row][column]:
                continue
            elif self._grid[row][column] != 0:
                uncovered[row][column] = True
                yield row, column
            else:
                uncovered[row][column] = True

                for dy, dx in Ordinal:
                    queue.put((row + dy, column + dx))
                yield row, column


# Square tile checkerboard.
@glooey.register_event_type("on_flag_place", "on_flag_remove", "on_second_pass")
class Checkerboard(glooey.Stack):
    def __init__(self, rows, columns, tile, mines, clear_start: bool = False):
        super().__init__()

        self.tile = tile
        self.mines = mines
        self.clear_start = clear_start

        self.rows = rows
        self.columns = columns

        height = self.columns * self.tile
        width = self.rows * self.tile

        self.grid = Minefield(self.rows, self.columns)
        if not clear_start:
            self.grid.generate(self.mines)

        self.revealed: list[list[bool]] = create_grid(self.rows, self.columns, False)
        self.has_started = False
        self.dispatch_clock_event = lambda dt: self.dispatch_event("on_second_pass", self)

        # Glooey
        self.set_size_hint(height, width)
        self.overlaps: list[glooey.Widget] = []

        # Background image
        board_img = create_checkerboard_image(height, width,
                                              self.tile, self.tile,
                                              Colour.LIGHT_BROWN, Colour.DARK_BROWN)
        self.board = glooey.Image(board_img)
        self.add(self.board)

        # Foreground image
        cover_img = create_checkerboard_image(height, width,
                                              self.tile, self.tile,
                                              Colour.LIGHT_GREEN, Colour.DARK_GREEN)
        self.cover = glooey.Image(cover_img)
        self.add(self.cover)

        # Pyglet sprites
        self.labels: list[Sprite] = []
        self.number_labels = [pyglet.image.create(self.tile, self.tile).get_texture()] \
                             + [pyglet.resource.image(f"{n}.png") for n in range(1, 10)]

        for num_img in self.number_labels[1:]:
            num_img.width = self.tile
            num_img.height = self.tile

        self.flags: dict = {}
        flag_image.width = self.tile
        flag_image.height = self.tile

        # Transparent pattern used to un-hide parts of the checkerboard.
        self.transparent_pattern = pyglet.image.create(self.tile, self.tile)

    def do_undraw(self):
        super().do_undraw()

        for lbl in self.labels:
            lbl.delete()

        for flag in self.flags:
            self.flags[flag].delete()

        if self.has_started:
            pyglet.clock.unschedule(self.dispatch_clock_event)

    def uncover(self, row, column):
        if not self.has_started:
            pyglet.clock.schedule_interval(self.dispatch_clock_event, 1)
            self.has_started = True

        self.revealed[row][column] = True

        num = self.grid[row][column]
        self.cover.image.blit_into(self.transparent_pattern,
                                   self.tile * column,
                                   self.tile * row,
                                   0)

        if num > 0 or num == Minefield.MINE:
            self.labels.append(Sprite(self.number_labels[num],
                                      column * self.tile,
                                      row * self.tile,
                                      group=self.cover.get_group(),
                                      batch=self.batch)
                               )
            self.labels[-1].scale = self.tile / self.labels[-1].height

    def uncover_all(self, diff: list[list[bool]]):
        iterations = 0
        for r in range(self.rows):
            for c in range(self.columns):
                if diff[r][c] and not self.revealed[r][c]:
                    self.uncover(r, c)
                    iterations += 1

        # Sound effects
        if iterations == 1:
            clear_sfx.play()
        elif iterations > 1:
            flood_sfx.play()

    def handle_mouse(self, x, y, button):
        # Reject mouse presses if another widget has already been pressed.
        for widget in self.overlaps:
            if widget.is_under_mouse(x, y) and widget.is_visible:
                return

        if button == mouse.LEFT:
            row = y // self.tile
            column = x // self.tile

            # Generate the minefield, ensuring the first revealed cell is not a mine.
            if self.grid.empty:
                self.grid.generate(self.mines, (row * self.grid.columns + column))

            # A player must remove a flag before revealing a cell.
            if (row, column) not in self.flags:
                diff = self.grid.minesweep(row, column)
                self.uncover_all(diff)
        elif button == mouse.MIDDLE:
            # Middle mouse button - uncover all - developer hotkey.
            if self.grid.empty:
                self.grid.generate(self.mines)

            diff = create_grid(self.rows, self.columns, True)
            self.uncover_all(diff)
        elif button == mouse.RIGHT:
            row = y // self.tile
            column = x // self.tile

            if (row, column) in self.flags:
                self.flags.pop((row, column))
                flag_remove_sfx.play()
                self.dispatch_event("on_flag_remove", self)
            else:
                flag_place_sfx.play()
                self.flags[row, column] = Sprite(flag_image,
                                                 column * self.tile,
                                                 row * self.tile,
                                                 group=OrderedGroup(2, parent=self.group),
                                                 batch=self.batch)
                self.dispatch_event("on_flag_place", self)

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        self.handle_mouse(x, y, buttons)

    def on_mouse_press(self, x, y, button, modifiers):
        self.handle_mouse(x, y, button)


class DifficultyMenu(glooey.VBox):
    Button = ui.SelectedDifficultyButton
    Dropdown = ui.DifficultiesDropdown

    custom_alignment = "top left"

    def __init__(self, difficulty: Difficulty):
        super().__init__()

        self.label = self.Button(difficulty)

        boxes = [ui.LabeledTickBox(difficulty) for difficulty in Difficulty]
        self.dropdown = self.Dropdown(boxes)
        self.dropdown.hide()

        self.pack(self.label)
        self.pack(self.dropdown)


def profile_uncover(minefield):
    import cProfile, pstats
    from pstats import SortKey

    with cProfile.Profile() as pr:
        minefield.uncover_adjacent(0, 0)

    with open("profile.txt", "w") as log:
        ps = pstats.Stats(pr, stream=log).strip_dirs()
        ps.sort_stats(SortKey.CUMULATIVE)
        ps.print_stats()

@autoprop
class Game(glooey.Gui):
    custom_one_child_gets_mouse = False

    def __init__(self, window, difficulty: Difficulty, *, cursor=None, hotspot=None, batch=None, group=None):
        super().__init__(window, cursor=cursor, hotspot=hotspot, batch=batch, group=group)
        self._difficulty = difficulty

        columns, rows, tile, mines, clear_start = DIFFICULTY_SETTINGS.get(self.difficulty)
        self.minefield = Checkerboard(rows, columns, tile, mines, clear_start=clear_start)

        # Playing layer
        self.playing_layer = glooey.VBox()
        self.add(self.playing_layer)

        # Header
        self.header = ui.HeaderBackground()
        self.playing_layer.pack(self.header)
        self.playing_layer.pack(self.minefield)

        self.relay_events_from(self.minefield, "on_flag_place")
        self.relay_events_from(self.minefield, "on_flag_remove")
        self.relay_events_from(self.minefield, "on_second_pass")

        # Counters
        # they are slightly more compressed & anti-aliased in the original.
        self.counters = ui.HeaderCenter()

        self.flag_icon = glooey.Image(flag_image, responsive=True)
        self.flag_icon.set_size_hint(38, 38)
        self.flag_counter = ui.StatisticWidget(str(mines))
        self.clock_icon = glooey.Image(clock_image, responsive=True)
        self.clock_icon.set_size_hint(38, 38)
        self.clock_counter = ui.StatisticWidget("000")

        self.counters.pack(self.flag_icon)
        self.counters.add(self.flag_counter)
        self.counters.pack(self.clock_icon)
        self.counters.add(self.clock_counter)

        self.add(self.counters)

        # Difficulty menu
        self.diff_menu = DifficultyMenu(Difficulty.EASY)
        self.add(self.diff_menu)

        self.minefield.overlaps.append(self.diff_menu.dropdown)

    def set_difficulty(self, value: Difficulty):
        self._difficulty = self.diff_menu.label.text = value
        columns, rows, tile, mines, clear_start = DIFFICULTY_SETTINGS.get(value)

        # Remove the minefield.
        self.playing_layer.remove(self.minefield)
        del self.minefield

        # Counters
        self.flag_counter.set_text(str(mines))
        self.clock_counter.set_text("000")

        self.window.width = columns * tile
        self.window.height = rows * tile + 60

        # Checkerboard
        self.minefield = Checkerboard(rows, columns, tile, mines, clear_start=clear_start)
        self.playing_layer.pack(self.minefield)

        self.minefield.overlaps.append(self.diff_menu.dropdown)

        self.relay_events_from(self.minefield, "on_flag_place")
        self.relay_events_from(self.minefield, "on_flag_remove")
        self.relay_events_from(self.minefield, "on_second_pass")

    def get_difficulty(self):
        return self._difficulty

    def on_flag_place(self, minefield):
        mines = DIFFICULTY_SETTINGS.get(self.difficulty).mines
        self.flag_counter.set_text(str(mines - len(minefield.flags)))

    def on_flag_remove(self, minefield):
        mines = DIFFICULTY_SETTINGS.get(self.difficulty).mines
        self.flag_counter.set_text(str(mines - len(minefield.flags)))

    def on_second_pass(self, widget):
        seconds = int(self.clock_counter.get_text())
        self.clock_counter.set_text("{!s:0>3}".format(seconds + 1))


def main():
    columns, rows, tile, mines, _ = DIFFICULTY_SETTINGS.get(Difficulty.EASY)

    window = Window(columns * tile, rows * tile + 60, caption="Google Minesweeeper")

    gui = Game(window, Difficulty.EASY)

    @gui.diff_menu.label.event
    def on_click(widget):
        if gui.diff_menu.dropdown.is_hidden:
            gui.diff_menu.dropdown.unhide()
        else:
            gui.diff_menu.dropdown.hide()

    @gui.diff_menu.label.event
    def on_mouse_enter(*_):
        window.set_mouse_cursor(window.get_system_mouse_cursor(Window.CURSOR_HAND))

    @gui.diff_menu.label.event
    def on_mouse_leave(*_):
        window.set_mouse_cursor(window.get_system_mouse_cursor(Window.CURSOR_DEFAULT))

    # profile_uncover(minefield)

    @gui.diff_menu.dropdown.event
    def on_selection():
        difficulty = gui.diff_menu.dropdown.get_selected_widget().text
        gui.set_difficulty(difficulty)

    pyglet.app.run()
