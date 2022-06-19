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
from pyglet.text import Label
from pyglet.window import mouse, Window

from minesweeper import ui
from minesweeper.shapes import RoundedRectangle, generate_dropdown_arrow
from minesweeper.positioning import Positioner


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
        self.cover = Sprite(img, group=self.group, batch=self.batch)

        self.labels = []
        self.number_labels = [pyglet.image.create(self.tile, self.tile).get_texture()] \
                             + [pyglet.resource.image(f"{n}.png")
                                for n in range(1, 10)]

        for num_img in self.number_labels[1:]:
            num_img.width = self.tile
            num_img.height = self.tile

        self.flags = {}
        self.flag_img = pyglet.resource.image("flag_icon.png")
        self.flag_img.width = self.tile
        self.flag_img.height = self.tile

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
                self.flags[row, column] = Sprite(self.flag_img,
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


class DifficultySelector(pyglet.event.EventDispatcher):
    label: Label
    arrow: pyglet.shapes.Triangle
    selector: RoundedRectangle

    dropdown: RoundedRectangle
    difficulty_boxes: list[pyglet.shapes.Rectangle]
    difficulty_labels: list[Label]
    tick: Sprite
    base_layer: int = 0

    tick_image = pyglet.resource.image("checkmark.png")

    def __init__(self, x, y, text: Difficulty, batch: Batch = None, group: Group = None):
        """ Create a multiple-choice dropdown menu to select the difficulty. """
        self._x = x
        self._y = y
        self._difficulty = text
        self.batch = batch
        self.group = group

        self.height = 30  # The height of the button.

        # Button
        self.label = Label(self.difficulty, x=self._x + 7, y=self._y + self.height // 2,
                           font_name="Roboto Medium", font_size=11.25, bold=True,
                           anchor_y='center', color=Colour.DIFFICULTY_LABEL,
                           group=OrderedGroup(DifficultySelector.base_layer + 2),
                           batch=self.batch)

        self.width = self.label.content_width + 7 + 20  # The width of the button.

        self.arrow = generate_dropdown_arrow(self._x + self.label.content_width + 7 + 6,
                                             self._y + 16, self.batch,
                                             OrderedGroup(
                                                 DifficultySelector.base_layer + 2))

        self.selector = RoundedRectangle(self._x, self._y, self.width, self.height, 5,
                                         batch=self.batch,
                                         group=OrderedGroup(
                                             DifficultySelector.base_layer + 1))

        # Dropdown difficulty options.
        self.difficulty_boxes = []
        self.difficulty_labels = []
        line_height = 23
        for i, difficulty in enumerate(Difficulty):
            self.difficulty_boxes.append(
                pyglet.shapes.Rectangle(self._x, self._y - line_height * (i + 1) - 5,
                                        102, line_height,
                                        color=Colour.DIFFICULTY_SELECTED.to_rgb(),
                                        batch=self.batch,
                                        group=OrderedGroup(
                                            DifficultySelector.base_layer + 4))
            )
            self.difficulty_boxes[-1].visible = False

            self.difficulty_labels.append(
                Label(difficulty, x=self._x + 28, y=self._y - 7 - (line_height * i),
                      font_name="Roboto Medium", font_size=11.25, bold=True,
                      anchor_y="top", color=Colour.DIFFICULTY_LABEL,
                      group=OrderedGroup(DifficultySelector.base_layer + 5),
                      batch=self.batch)
            )
            self.difficulty_labels[-1].visible = False

        # Selected difficulty tick.
        self.tick = Sprite(DifficultySelector.tick_image, self._x, self._y - 5,
                           group=OrderedGroup(DifficultySelector.base_layer + 5),
                           batch=self.batch)
        self.tick.y -= DifficultySelector.tick_image.height

        self.tick_positions = tuple((int(self.tick.y) - line_height * i)
                                    for i in range(len(Difficulty)))

        self.tick.y = self.tick_positions[list(Difficulty).index(self.difficulty)]
        self.tick.visible = False

        # Dropdown menu
        dropdown_height = (line_height * len(Difficulty) - 1) + 10
        self.dropdown = RoundedRectangle(self._x, self._y - dropdown_height,
                                         102, dropdown_height, 8,
                                         batch=self.batch,
                                         group=OrderedGroup(
                                             DifficultySelector.base_layer + 3))
        self.dropdown.visible = False

    def __del__(self):
        self.label.delete()
        for difficulty_label in self.difficulty_labels:
            difficulty_label.delete()

    def _update_button(self):
        self.width = self.label.content_width + 7 + 20

        self.label.x = self._x + 7
        self.label.y = self._y + self.height // 2

        self.arrow = generate_dropdown_arrow(self._x + self.label.content_width + 7 + 6,
                                             self._y + 16, self.batch,
                                             OrderedGroup(
                                                 DifficultySelector.base_layer + 3))

        self.selector.x = self._x
        self.selector.y = self._y
        self.selector.width = self.width
        self.selector.height = self.height

    def _update_dropdown(self):
        # Dropdown menu
        self.dropdown.x = self._x
        self.dropdown.y = self._y - self.dropdown.height

        # Dropdown difficulty options.
        line_height = 23
        for i in range(len(Difficulty)):
            self.difficulty_boxes[i].x = self._x
            self.difficulty_boxes[i].y = self._y - line_height * (i + 1) - 5

            self.difficulty_labels[i].x = self._x + 28
            self.difficulty_labels[i].y = self._y - 7 - (line_height * i)

        # Selected difficulty tick.
        self.tick.x = self._x
        self.tick.y = self._y - 5
        self.tick.y -= DifficultySelector.tick_image.height

        self.tick_positions = tuple((int(self.tick.y) - line_height * i)
                                    for i in range(len(Difficulty)))
        self.tick.y = self.tick_positions[list(Difficulty).index(self.difficulty)]

    @property
    def difficulty(self):
        return self._difficulty

    @difficulty.setter
    def difficulty(self, value):
        self.label.text = self._difficulty = value
        self.dispatch_event("on_difficulty_change", self._difficulty)
        self._update_button()

    @property
    def x(self):
        return self._x

    @x.setter
    def x(self, value):
        self._x = value
        self._update_button()
        self._update_dropdown()

    @property
    def y(self):
        return self._y

    @y.setter
    def y(self, value):
        self._y = value
        self._update_button()
        self._update_dropdown()

    @property
    def aabb(self):
        return self._x, self._y, self._x + self.width, self._y + self.height

    def collides_with(self, x, y):
        if self._x < x < self._x + self.width and \
                self._y < y < self._y + self.height:
            return self.selector
        elif self.dropdown.visible:
            if self.dropdown.x < x < self.dropdown.x + self.dropdown.width and \
                    self.dropdown.y < y < self.dropdown.y + self.dropdown.height:
                for i, box in enumerate(self.difficulty_boxes):
                    if box.x < x < box.x + box.width and \
                            box.y < y < box.y + box.height:
                        return box

                return self.dropdown

    def on_mouse_press(self, x, y, button, modifiers):
        collision = self.collides_with(x, y)
        if not collision:
            return pyglet.event.EVENT_UNHANDLED

        if button == mouse.LEFT:
            if collision == self.selector:
                self.dropdown.visible ^= True
                self.difficulty_boxes[0].visible = self.dropdown.visible

                for difficulty in self.difficulty_labels:
                    difficulty.visible ^= True

                self.tick.visible ^= True
            elif collision in self.difficulty_boxes:
                i = self.difficulty_boxes.index(collision)
                self.difficulty = list(Difficulty)[i]

        return pyglet.event.EVENT_HANDLED

    def on_mouse_motion(self, x, y, dx, dy):
        collision = self.collides_with(x, y)

        if collision == self.selector:
            self.dispatch_event("on_cursor_change", Window.CURSOR_HAND)
        else:
            self.dispatch_event("on_cursor_change", Window.CURSOR_DEFAULT)

        for box in self.difficulty_boxes:
            box.visible = (box == collision)

        if collision:
            return pyglet.event.EVENT_HANDLED
        else:
            return pyglet.event.EVENT_UNHANDLED

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        collision = self.collides_with(x, y)

        if collision != self.selector:
            self.dispatch_event("on_cursor_change", Window.CURSOR_DEFAULT)

        if not collision:
            return pyglet.event.EVENT_UNHANDLED

        return pyglet.event.EVENT_HANDLED


DifficultySelector.register_event_type("on_mouse_press")
DifficultySelector.register_event_type("on_motion_motion")
DifficultySelector.register_event_type("on_mouse_drag")

DifficultySelector.register_event_type("on_cursor_change")
DifficultySelector.register_event_type("on_difficulty_change")


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
    flag_image = pyglet.resource.image("flag_icon.png")
    flag_image.width, flag_image.height = 38, 38

    clock_image = pyglet.resource.image("clock_icon.png")
    clock_image.width, clock_image.height = 38, 38

    width, height, tile, mines, _ = DIFFICULTY_SETTINGS.get(Difficulty.EASY)

    window = Window(width, height + 60,
                    caption="Google Minesweeeper")
    batch = pyglet.graphics.Batch()
    gui = glooey.Gui(window, batch=batch, group=OrderedGroup(0))

    # Header
    header = ui.HeaderBackground()
    gui.add(header)

    # counters are slightly more compressed & anti-aliased in the original.
    counters = ui.HeaderCenter()
    gui.add(counters)

    flag_icon = glooey.Image(flag_image)
    flag_counter = ui.StatisticWidget("10")
    clock_icon = glooey.Image(clock_image)
    clock_counter = ui.StatisticWidget("000")

    counters.pack(flag_icon)
    counters.add(flag_counter)
    counters.pack(clock_icon)
    counters.add(clock_counter)

    difficulty_menu = DifficultySelector(16, height + 15, Difficulty.EASY, batch)

    # Checkerboard
    board, minefield = create_checkerboard(Difficulty.EASY, batch)
    window.push_handlers(minefield)
    window.push_handlers(difficulty_menu)

    # profile_uncover(minefield)

    @difficulty_menu.event
    def on_difficulty_change(difficulty):
        nonlocal difficulty_menu, minefield, board, window, flag_image, clock_image

        width, height, tile, mines, _ = DIFFICULTY_SETTINGS.get(difficulty)

        flag_image.width, flag_image.height = 38, 38
        clock_image.width, clock_image.height = 38, 38

        window.width = width
        window.height = height + 60

        # Header
        difficulty_menu.x = 16
        difficulty_menu.y = height + 15

        # Checkerboard
        board, minefield = create_checkerboard(difficulty, batch)

        window.push_handlers(minefield)
        window.push_handlers(difficulty_menu)

    @difficulty_menu.event
    def on_cursor_change(cursor):
        window.set_mouse_cursor(window.get_system_mouse_cursor(cursor))

    pyglet.app.run()
