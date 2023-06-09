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

import pyglet
from minesweeper import ui

pyglet.options["win32_gdi_font"] = True

from pyglet.graphics import Group
from pyglet.image import SolidColorImagePattern
from pyglet.image import TextureRegion, Texture
from pyglet.sprite import Sprite
from pyglet.shapes import Rectangle
from pyglet.window import mouse, Window


class Colour(tuple, Enum):
    _hint = tuple[int, int, int, int]

    def to_rgb(self):
        return self[0], self[1], self[2]

    LIGHT_GREEN: _hint = (170, 215, 81, 255)
    LIGHT_GREEN_HOVER: _hint = (191, 225, 125, 255)

    DARK_GREEN: _hint = (162, 209, 73, 255)
    DARK_GREEN_HOVER: _hint = (185, 221, 119, 255)

    LINE_GREEN: _hint = (135, 175, 58, 255)

    HEADER_GREEN: _hint = (74, 117, 44, 255)

    LIGHT_BROWN: _hint = (229, 194, 159, 255)
    LIGHT_BROWN_HOVER: _hint = (236, 209, 183, 255)

    DARK_BROWN: _hint = (215, 184, 153, 255)
    DARK_BROWN_HOVER: _hint = (225, 202, 179, 255)

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
                                      "guaranteed_start", "line_width"])

DIFFICULTY_SETTINGS = {
    Difficulty.EASY: DifficultySettingsTuple(10, 8, 45, 10, True, 4),
    Difficulty.MEDIUM: DifficultySettingsTuple(18, 14, 30, 40, True, 2),
    Difficulty.HARD: DifficultySettingsTuple(24, 20, 25, 99, True, 2),
    Difficulty.EXTREME: DifficultySettingsTuple(38, 30, 20, 300, True, 1),
    Difficulty.LOTTERY: DifficultySettingsTuple(5, 5, 100, 24, False, 8)
}

# Specify resource paths.
BASEDIR = os.path.dirname(os.path.abspath(__file__))

pyglet.resource.path = [os.path.join(BASEDIR, "assets"),
                        os.path.join(BASEDIR, "assets", "numbers"),
                        os.path.join(BASEDIR, "assets", "sfx"),
                        os.path.join(BASEDIR, "assets", "fonts", "Roboto")]
pyglet.resource.reindex()

# Images
flag_image = pyglet.resource.image("flag_icon.png")
clock_image = pyglet.resource.image("clock_icon.png")

# Sound effects
clear_sfx = pyglet.resource.media("clear.mp3", streaming=False)
flood_sfx = pyglet.resource.media("flood.mp3", streaming=False)

one_reveal_sfx = pyglet.resource.media("1.mp3", streaming=False)
two_reveaL_sfx = pyglet.resource.media("2.mp3", streaming=False)
three_reveal_sfx = pyglet.resource.media("3.mp3", streaming=False)
four_reveal_sfx = pyglet.resource.media("4.mp3", streaming=False)

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

        A minefield is a 2-dimensional list where each cell describes how
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


# Square tile checkerboard.
class Checkerboard(pyglet.event.EventDispatcher):
    def __init__(self, x, y, rows, columns, tile, mines,
                 clear_start: bool = False, line_width: int = 2,
                 batch=None, group=None):
        super().__init__()

        self.x = x
        self.y = y
        self.tile = tile
        self.mines = mines
        self.clear_start = clear_start
        self.batch = batch or pyglet.graphics.get_default_batch()
        self.group = group or pyglet.graphics.get_default_group()

        self.rows = rows
        self.columns = columns
        self.line_width = line_width

        height = self.rows * self.tile
        width = self.columns * self.tile

        self.grid = Minefield(self.rows, self.columns)
        if not clear_start:
            self.grid.generate(self.mines)

        self.revealed: list[list[bool]] = create_grid(self.rows, self.columns, False)
        self.has_started = False
        self.dispatch_clock_event = lambda dt: self.dispatch_event("on_second_pass")

        # Transparent pattern
        self.transparent_pattern = pyglet.image.create(self.tile, self.tile)

        # Background image
        board_img = create_checkerboard_image(width, height,
                                              self.tile, self.tile,
                                              Colour.LIGHT_BROWN, Colour.DARK_BROWN)
        self.board = Sprite(board_img,
                            batch=self.batch,
                            group=Group(0, parent=self.group))

        # Background highlight image
        self.light_brown_hovered_tile = SolidColorImagePattern(Colour.LIGHT_BROWN_HOVER).create_image(self.tile,
                                                                                                      self.tile)
        self.dark_brown_hovered_tile = SolidColorImagePattern(Colour.DARK_BROWN_HOVER).create_image(self.tile,
                                                                                                    self.tile)

        self.board_highlight = Sprite(self.transparent_pattern,
                                      batch=self.batch,
                                      group=Group(1, parent=self.group))

        # Foreground image
        cover_img = create_checkerboard_image(width, height,
                                              self.tile, self.tile,
                                              Colour.LIGHT_GREEN, Colour.DARK_GREEN)
        self.cover = Sprite(cover_img,
                            batch=self.batch,
                            group=Group(2, parent=self.group))

        # Cover highlight image
        self.light_green_hovered_tile = SolidColorImagePattern(Colour.LIGHT_GREEN_HOVER).create_image(self.tile,
                                                                                                      self.tile)
        self.dark_green_hovered_tile = SolidColorImagePattern(Colour.DARK_GREEN_HOVER).create_image(self.tile,
                                                                                                    self.tile)

        self.cover_highlight = Sprite(self.transparent_pattern,
                                      batch=self.batch,
                                      group=Group(3, parent=self.group))

        self.particle_layer = Sprite(self.transparent_pattern,
                                     batch=self.batch,
                                     group=Group(4, parent=self.group))

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

        self.lines: list[Rectangle] = []
        self.particles: list[TileParticle] = []

    def delete(self):
        # Sprites
        self.board.delete()
        self.board_highlight.delete()
        self.cover.delete()
        self.cover_highlight.delete()
        self.particle_layer.delete()

        for lbl in self.labels:
            lbl.delete()

        for flag in self.flags:
            self.flags[flag].delete()

        for line in self.lines:
            line.delete()

        for particle in self.particles:
            particle.delete()

        # Events
        if self.has_started:
            pyglet.clock.unschedule(self.dispatch_clock_event)
            pyglet.clock.unschedule(self.animate_particles)

    def uncover(self, row, column):
        if not self.has_started:
            pyglet.clock.schedule_interval(self.dispatch_clock_event, 1)
            pyglet.clock.schedule_interval(self.animate_particles, 1 / 30)
            self.has_started = True

        self.revealed[row][column] = True

        # Cut out the appropriate part of the cover image.
        self.cover.image.blit_into(self.transparent_pattern,
                                   self.tile * column,
                                   self.tile * row,
                                   0)

        # Create particle effect of tile disappearing
        particle = TileParticle(column * self.tile, row * self.tile,
                                self.tile, self.tile,
                                color=(Colour.DARK_GREEN, Colour.LIGHT_GREEN)[(row + column) % 2].to_rgb(),
                                batch=self.batch,
                                group=self.particle_layer.group)
        self.particles.append(particle)

        # Remove flag in that position.
        if (row, column) in self.flags:
            self.flags.pop((row, column))
            self.dispatch_event("on_flag_remove", self)

        # Add number label.
        num = self.grid[row][column]
        if num > 0 or num == Minefield.MINE:
            label = Sprite(self.number_labels[num],
                           column * self.tile,
                           row * self.tile,
                           group=self.cover_highlight.group,
                           batch=self.batch)
            label.scale = self.tile / label.height

            self.labels.append(label)

    def uncover_all(self, diff: list[list[bool]]) -> int:
        iterations = 0
        for r in range(self.rows):
            for c in range(self.columns):
                if diff[r][c] and not self.revealed[r][c]:
                    self.uncover(r, c)
                    iterations += 1

        if iterations > 0:
            # Sound effects
            if iterations == 1:
                clear_sfx.play()
            elif iterations > 1:
                flood_sfx.play()

        return iterations

    def draw_border(self, row, column):
        # Find the cells that border covered cells and draw the appropriate border.
        # 4 pixel border on Easy
        # 2 pixel border on Medium and Hard

        line_kwargs = dict(color=Colour.LINE_GREEN.to_rgb(),
                           batch=self.batch,
                           group=self.cover_highlight.group)

        is_north_valid = row + 1 < self.rows
        is_south_valid = row - 1 >= 0
        is_east_valid = column + 1 < self.columns
        is_west_valid = column - 1 >= 0

        north = not self.revealed[row + 1][column] if is_north_valid else None
        north_east = not self.revealed[row + 1][column + 1] if is_north_valid and is_east_valid else None
        east = not self.revealed[row][column + 1] if is_east_valid else None
        south_east = not self.revealed[row - 1][column + 1] if is_south_valid and is_east_valid else None
        south = not self.revealed[row - 1][column] if is_south_valid else None
        south_west = not self.revealed[row - 1][column - 1] if is_south_valid and is_west_valid else None
        west = not self.revealed[row][column - 1] if is_west_valid else None
        north_west = not self.revealed[row + 1][column - 1] if is_north_valid and is_west_valid else None

        x = column * self.tile
        y = row * self.tile

        if north:
            self.lines.append(
                Rectangle(x, y + self.tile - self.line_width,
                          self.tile, self.line_width, **line_kwargs)
            )
        if north_east:
            self.lines.append(
                Rectangle(x + self.tile - self.line_width,
                          y + self.tile - self.line_width,
                          self.line_width, self.line_width, **line_kwargs)
            )
        if east:
            self.lines.append(
                Rectangle(x + self.tile - self.line_width, y,
                          self.line_width, self.tile, **line_kwargs)
            )
        if south_east:
            self.lines.append(
                Rectangle(x + self.tile - self.line_width, y,
                          self.line_width, self.line_width, **line_kwargs)
            )
        if south:
            self.lines.append(
                Rectangle(x, y,
                          self.tile, self.line_width, **line_kwargs)
            )
        if south_west:
            self.lines.append(
                Rectangle(x, y,
                          self.line_width, self.line_width, **line_kwargs)
            )
        if west:
            self.lines.append(
                Rectangle(x, y,
                          self.line_width, self.tile, **line_kwargs)
            )
        if north_west:
            self.lines.append(
                Rectangle(x, y + self.tile - self.line_width,
                          self.line_width, self.line_width, **line_kwargs)
            )

    def draw_borders(self):
        self.lines.clear()

        for row in range(self.rows):
            for column in range(self.columns):
                if self.revealed[row][column]:
                    self.draw_border(row, column)

    def update_highlight(self, row, column):
        self.cover_highlight.y = row * self.tile
        self.cover_highlight.x = column * self.tile

        self.board_highlight.y = row * self.tile
        self.board_highlight.x = column * self.tile

        self.cover_highlight.image = self.transparent_pattern
        self.board_highlight.image = self.transparent_pattern

        if row > self.rows - 1 or column > self.columns - 1:
            return

        if column % 2 + row % 2 == 1:
            if not self.revealed[row][column]:
                self.cover_highlight.image = self.light_green_hovered_tile
                self.board_highlight.image = self.transparent_pattern
            elif self.grid[row][column] != 0:
                self.cover_highlight.image = self.transparent_pattern
                self.board_highlight.image = self.light_brown_hovered_tile
        else:
            if not self.revealed[row][column]:
                self.cover_highlight.image = self.dark_green_hovered_tile
                self.board_highlight.image = self.transparent_pattern
            elif self.grid[row][column] != 0:
                self.cover_highlight.image = self.transparent_pattern
                self.board_highlight.image = self.dark_brown_hovered_tile

    def minesweep_from_cell(self, row, column):
        # Generate the minefield, ensuring the first revealed cell is not a mine.
        if self.grid.empty:
            self.grid.generate(self.mines, (row * self.grid.columns + column))

        # A player must remove a flag before revealing a cell.
        if (row, column) not in self.flags and \
                (self.grid.valid_index(row, column) and not self.revealed[row][column]):
            diff = self.grid.minesweep(row, column)
            iterations = self.uncover_all(diff)
            self.update_highlight(row, column)
            self.draw_borders()
            if iterations > 0:
                if self.grid[row][column] == 1:
                    one_reveal_sfx.play()
                elif self.grid[row][column] == 2:
                    two_reveaL_sfx.play()
                elif self.grid[row][column] == 3:
                    three_reveal_sfx.play()
                elif self.grid[row][column] == 4:
                    four_reveal_sfx.play()
                elif self.grid[row][column] == Minefield.MINE:
                    print("Fail!")  # Mine hit - Fail

    def on_mouse_press(self, x, y, button, modifiers):
        # Reject mouse presses if another widget has already been pressed.
        if button == mouse.LEFT:
            row = y // self.tile
            column = x // self.tile
            self.dispatch_event("on_first_interaction")
            self.minesweep_from_cell(row, column)
        elif button == mouse.MIDDLE:
            row = y // self.tile
            column = x // self.tile
            self.dispatch_event("on_first_interaction")

            # Middle mouse button - uncover all - developer hotkey.
            if self.grid.empty:
                self.grid.generate(self.mines)

            diff = create_grid(self.rows, self.columns, True)
            self.uncover_all(diff)
            self.update_highlight(row, column)
            self.lines.clear()
        elif button == mouse.RIGHT:
            row = y // self.tile
            column = x // self.tile
            self.dispatch_event("on_first_interaction")

            # Place or Remove flags
            if (row, column) in self.flags:
                self.flags.pop((row, column))
                flag_remove_sfx.play()
                self.dispatch_event("on_flag_remove", self)
            elif not self.revealed[row][column]:
                flag_place_sfx.play()
                flag_image.width = self.tile
                flag_image.height = self.tile
                self.flags[row, column] = Sprite(flag_image,
                                                 column * self.tile,
                                                 row * self.tile,
                                                 group=Group(4, parent=self.group),
                                                 batch=self.batch)
                self.dispatch_event("on_flag_place", self)

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        if buttons == mouse.LEFT:
            row = y // self.tile
            column = x // self.tile
            self.update_highlight(row, column)
            self.dispatch_event("on_first_interaction")
            self.minesweep_from_cell(row, column)

    def on_mouse_motion(self, x, y, dx, dy):
        row = y // self.tile
        column = x // self.tile
        self.update_highlight(row, column)

    def on_mouse_leave(self, x, y):
        self.cover_highlight.image = self.transparent_pattern
        self.board_highlight.image = self.transparent_pattern

    def animate_particles(self, _):
        for particle in self.particles:
            particle.animate()

        self.particles = [particle for particle in self.particles if particle.scale != 0]


Checkerboard.register_event_type("on_flag_place")
Checkerboard.register_event_type("on_flag_remove")
Checkerboard.register_event_type("on_second_pass")
Checkerboard.register_event_type("on_first_interaction")


def profile_uncover(minefield):
    import cProfile, pstats
    from pstats import SortKey

    with cProfile.Profile() as pr:
        minefield.uncover_adjacent(0, 0)

    with open("profile.txt", "w") as log:
        ps = pstats.Stats(pr, stream=log).strip_dirs()
        ps.sort_stats(SortKey.CUMULATIVE)
        ps.print_stats()


class Game(Window):
    def __init__(self, difficulty: Difficulty, *, batch=None, group=None):
        self._difficulty = difficulty

        columns, rows, tile, mines, clear_start, line_width = DIFFICULTY_SETTINGS.get(self._difficulty)
        super().__init__(columns * tile, rows * tile + 60, caption="Google Minesweeeper")

        self.batch = batch or pyglet.graphics.get_default_batch()
        self.group = group or pyglet.graphics.get_default_group()

        # Checkerboard
        self.checkerboard = Checkerboard(0, 0, rows, columns, tile, mines, clear_start, line_width,
                                         batch=self.batch, group=Group(0))

        # Tutorial
        self.tutorial = ui.Tutorial(self, self.width // 2, self.height // 2 + 45,
                                    batch=self.batch, group=self.group)

        # Header
        self.header = Rectangle(0, rows * tile, columns * tile, 60, color=Colour.HEADER_GREEN,
                                batch=self.batch, group=Group(3))

        self.counters = ui.Counters(self, batch=self.batch, group=Group(4))

        # Difficulty menu

        # self._difficulty
        self.diff_menu = ui.DifficultyMenu(self, batch=self.batch, group=Group(5))

        # Event Handling
        self._setup_event_stack()

    def _setup_event_stack(self):
        self.push_handlers(self.checkerboard)

        self.push_handlers(self.diff_menu)
        self.push_handlers(self.diff_menu.button)
        self.push_handlers(self.diff_menu.dropdown)

        for child in self.diff_menu.dropdown.children:
            self.push_handlers(child)
            child.push_handlers(self)

        # Event => self.diff_menu.dropdown => self.diff_menu.button => self.diff_menu => self.checkerboard

        self.checkerboard.push_handlers(self.counters)
        self.checkerboard.push_handlers(self.tutorial)

    def _remove_event_stack(self):
        self.remove_handlers(self.checkerboard)

        self.remove_handlers(self.diff_menu)
        self.remove_handlers(self.diff_menu.button)
        self.remove_handlers(self.diff_menu.dropdown)

        for child in self.diff_menu.dropdown.children:
            self.remove_handlers(child)
            child.remove_handlers(self)

        self.checkerboard.remove_handlers(self.counters)
        self.checkerboard.remove_handlers(self.tutorial)

    @property
    def difficulty(self):
        return self._difficulty

    @difficulty.setter
    def difficulty(self, value: Difficulty):
        self._difficulty = value
        # self.diff_menu.label.text = value
        columns, rows, tile, mines, clear_start, line_width = DIFFICULTY_SETTINGS.get(value)

        self.width = columns * tile
        self.height = rows * tile + 60

        # Header
        self.header.y = rows * tile
        self.header.width = columns * tile

        # Counters
        self.counters.repack()

        self.counters.flag_counter.text = str(mines)
        self.counters.clock_counter.text = "000"

        # Difficulty Menu
        self.diff_menu.repack()

        # Checkerboard
        self._remove_event_stack()

        self.checkerboard.delete()
        del self.checkerboard

        self.checkerboard = Checkerboard(0, 0, rows, columns, tile, mines,
                                         clear_start=clear_start, line_width=line_width,
                                         batch=self.batch, group=Group(0))
        self._setup_event_stack()

        self.tutorial.group.visible = False

    def on_draw(self):
        self.clear()
        self.batch.draw()

    def on_select(self, widget):
        difficulty = Difficulty(widget.label.text)
        self.difficulty = difficulty


def main():
    game = Game(Difficulty.MEDIUM)

    pyglet.app.run()
