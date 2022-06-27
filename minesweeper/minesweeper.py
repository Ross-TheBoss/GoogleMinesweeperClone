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
                                     ["width", "height", "tile", "mines",
                                      "guaranteed_start"])

DIFFICULTY_SETTINGS = {
    Difficulty.EASY: DifficultySettingsTuple(450, 360, 45, 10, True),
    Difficulty.MEDIUM: DifficultySettingsTuple(540, 420, 30, 40, True),
    Difficulty.HARD: DifficultySettingsTuple(600, 500, 25, 99, True),
    Difficulty.EXTREME: DifficultySettingsTuple(760, 600, 20, 300, True),
    Difficulty.LOTTERY: DifficultySettingsTuple(500, 500, 100, 24, False)
}

# Specify resource paths.
BASEDIR = os.path.dirname(os.path.abspath(__file__))

pyglet.resource.path = [os.path.join(BASEDIR, "assets"),
                        os.path.join(BASEDIR, "assets", "numbers"),
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

    def minesweep(self, row, column,
                  uncovered: Optional[list[list[bool]]] = None) -> list[list[bool]]:
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
class Checkerboard(pyglet.event.EventDispatcher):
    def __init__(self, width, height, tile, mines, clear_start: bool = False,
                 group: Optional[Group] = None, batch: Optional[Batch] = None):
        super().__init__()

        self.width = width
        self.height = height
        self.tile = tile
        self.mines = mines
        self.clear_start = clear_start

        self.group = group
        self.batch = batch

        self.rows = self.height // self.tile
        self.columns = self.width // self.tile

        self.grid = Minefield(self.rows, self.columns)
        if not clear_start:
            self.grid.generate(self.mines)

        self.revealed: list[list[bool]] = create_grid(self.rows, self.columns, False)

        img = create_checkerboard_image(self.width, self.height, self.tile, self.tile,
                                        Colour.LIGHT_GREEN, Colour.DARK_GREEN)
        self.cover = Sprite(img, group=group, batch=self.batch)

        self.labels = []
        self.number_labels = [pyglet.image.create(self.tile, self.tile).get_texture()] \
                             + [pyglet.resource.image(f"{n}.png")
                                for n in range(1, 10)]

        for num_img in self.number_labels[1:]:
            num_img.width = self.tile
            num_img.height = self.tile

        self.flags = {}
        flag_image.width = self.tile
        flag_image.height = self.tile

        # Transparent pattern used to un-hide parts of the checkerboard.
        self.transparent_pattern = pyglet.image.create(self.tile, self.tile)

    def uncover(self, row, column):
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
                                      group=OrderedGroup(1),
                                      batch=self.batch)
                               )
            self.labels[-1].scale = self.tile / self.labels[-1].height

    def uncover_all(self, diff: list[list[bool]]):
        for r in range(self.rows):
            for c in range(self.columns):
                if diff[r][c]:
                    self.uncover(r, c)

    def handle_mouse(self, x, y, button):
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
            if self.grid.empty:
                self.grid.generate(self.mines)

            diff = create_grid(self.rows, self.columns, True)
            self.uncover_all(diff)
        elif button == mouse.RIGHT:
            row = y // self.tile
            column = x // self.tile

            if (row, column) in self.flags:
                self.flags.pop((row, column))
            else:
                self.flags[row, column] = Sprite(flag_image,
                                                 column * self.tile,
                                                 row * self.tile,
                                                 group=OrderedGroup(2),
                                                 batch=self.batch)

    def on_mouse_press(self, x, y, button, modifiers):
        if 0 < x < self.width and 0 < y < self.height:
            self.handle_mouse(x, y, button)

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        if 0 < x < self.width and 0 < y < self.height:
            self.handle_mouse(x, y, buttons)


Checkerboard.register_event_type("on_mouse_press")
Checkerboard.register_event_type("on_mouse_drag")


def profile_uncover(minefield):
    import cProfile, pstats
    from pstats import SortKey

    with cProfile.Profile() as pr:
        minefield.uncover_adjacent(0, 0)

    with open("profile.txt", "w") as log:
        ps = pstats.Stats(pr, stream=log).strip_dirs()
        ps.sort_stats(SortKey.CUMULATIVE)
        ps.print_stats()


def create_checkerboard(difficulty: Difficulty, batch: Batch):
    settings = DIFFICULTY_SETTINGS.get(difficulty, None)
    if settings is None:
        raise NotImplementedError(f"{difficulty} difficulty not implemented.")

    width, height, tile, mines, clear_start = settings

    # Checkerboard

    # Background
    board_img = create_checkerboard_image(width, height,
                                          tile, tile,
                                          Colour.LIGHT_BROWN, Colour.DARK_BROWN)
    board = Sprite(board_img, batch=batch,
                   group=OrderedGroup(0))

    # Foreground
    minefield = Checkerboard(width, height,
                             tile, mines, clear_start=clear_start,
                             batch=batch, group=OrderedGroup(2))

    return board, minefield


def main():
    width, height, tile, mines, _ = DIFFICULTY_SETTINGS.get(Difficulty.EASY)

    window = Window(width, height + 60, caption="Google Minesweeeper")
    batch = pyglet.graphics.Batch()

    # Checkerboard
    board, minefield = create_checkerboard(Difficulty.EASY, batch)
    window.push_handlers(minefield)

    gui = glooey.Gui(window, batch=batch, group=OrderedGroup(10))

    # Header
    header = ui.HeaderBackground()
    gui.add(header)

    # counters are slightly more compressed & anti-aliased in the original.
    counters = ui.HeaderCenter()
    gui.add(counters)

    flag_icon = glooey.Image(flag_image, responsive=True)
    flag_icon.set_size_hint(38, 38)
    flag_counter = ui.StatisticWidget("10")
    clock_icon = glooey.Image(clock_image, responsive=True)
    clock_icon.set_size_hint(38, 38)
    clock_counter = ui.StatisticWidget("000")

    counters.pack(flag_icon)
    counters.add(flag_counter)
    counters.pack(clock_icon)
    counters.add(clock_counter)

    diff_menu = glooey.VBox()
    gui.add(diff_menu)

    diff_label = ui.SelectedDifficultyButton(Difficulty.EASY)
    diff_menu.pack(diff_label)

    boxes = [ui.LabeledTickBox(difficulty) for difficulty in Difficulty]
    diff_dropdown = ui.DifficultiesDropdown(boxes)
    diff_dropdown.hide()

    diff_menu.pack(diff_dropdown)

    @diff_label.event
    def on_click(widget):
        if diff_dropdown.is_hidden:
            diff_dropdown.unhide()
        else:
            diff_dropdown.hide()

    @diff_label.event
    def on_mouse_enter(x, y):
        window.set_mouse_cursor(window.get_system_mouse_cursor(Window.CURSOR_HAND))

    @diff_label.event
    def on_mouse_leave(x, y):
        window.set_mouse_cursor(window.get_system_mouse_cursor(Window.CURSOR_DEFAULT))

    # profile_uncover(minefield)

    @diff_dropdown.event
    def on_selection():
        nonlocal diff_menu, minefield, board, window

        difficulty = diff_dropdown.vbox.children[diff_dropdown.selected_index].text
        diff_label.text = difficulty

        width, height, tile, mines, _ = DIFFICULTY_SETTINGS.get(difficulty)

        window.width = width
        window.height = height + 60

        # Checkerboard
        board, minefield = create_checkerboard(difficulty, batch)

        window.push_handlers(minefield)

    pyglet.app.run()
