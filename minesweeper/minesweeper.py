"""
A Google Minesweeper clone made using pyglet.
"""

import random
import os.path

from queue import Queue
from typing import Optional

import pyglet
from pyglet.media import StaticSource

from minesweeper import ui
from minesweeper.constants import Difficulty, DIFFICULTY_SETTINGS, SHOW_FPS, Colour, Ordinal, MINE_COLOURS
from minesweeper.shapes import TileParticle
from minesweeper.sprites import CheckerboardSprite, MinefieldSprite

pyglet.options["win32_gdi_font"] = True

from pyglet.graphics import Group
from pyglet.image import SolidColorImagePattern, AbstractImage
from pyglet.sprite import Sprite
from pyglet.shapes import Rectangle
from pyglet.window import mouse, Window, FPSDisplay

# Specify resource paths.
BASEDIR = os.path.dirname(os.path.abspath(__file__))

pyglet.resource.path = [os.path.join(BASEDIR, "shaders"),
                        os.path.join(BASEDIR, "assets"),
                        os.path.join(BASEDIR, "assets", "numbers"),
                        os.path.join(BASEDIR, "assets", "sfx")]
pyglet.resource.reindex()

# Images
flag_image = pyglet.resource.image("flag_icon.png")

# Sound effects
clear_sfx: StaticSource = pyglet.resource.media("clear.mp3", streaming=False)
flood_sfx: StaticSource = pyglet.resource.media("flood.mp3", streaming=False)

one_reveal_sfx: StaticSource = pyglet.resource.media("1.mp3", streaming=False)
two_reveaL_sfx: StaticSource = pyglet.resource.media("2.mp3", streaming=False)
three_reveal_sfx: StaticSource = pyglet.resource.media("3.mp3", streaming=False)
four_reveal_sfx: StaticSource = pyglet.resource.media("4.mp3", streaming=False)

flag_place_sfx: StaticSource = pyglet.resource.media("flag place.mp3", streaming=False)
flag_remove_sfx: StaticSource = pyglet.resource.media("flag remove.mp3", streaming=False)


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


# Square tile checkerboard.
class Checkerboard(pyglet.event.EventDispatcher):
    def __init__(self, x, y, rows, columns, tile, mines,
                 clear_start: bool = False, line_width: int = 2,
                 muted: bool = False, batch=None, group=None):
        super().__init__()

        self.x = x
        self.y = y

        self.rows = rows
        self.columns = columns

        self.tile = tile
        self.mines = mines
        self.clear_start = clear_start
        self.line_width = line_width

        self.muted = muted

        self.batch = batch or pyglet.graphics.get_default_batch()
        self.group = group or pyglet.graphics.get_default_group()

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

        # Background image mask
        board_img = pyglet.image.create(width, height, SolidColorImagePattern(Colour.BLACK))
        self.board = CheckerboardSprite(board_img,
                                        color1=Colour.LIGHT_BROWN, color2=Colour.DARK_BROWN,
                                        tile_size=self.tile,
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

        number_layer_img = pyglet.image.Texture.create(columns * 100, rows * 100, blank_data=False)
        self.number_layer = Sprite(number_layer_img,
                                   batch=self.batch,
                                   group=Group(2, parent=self.group))
        self.number_layer.scale = self.tile / 100

        # Foreground image mask
        cover_img = pyglet.image.create(width, height, SolidColorImagePattern(Colour.BLACK))
        self.cover = CheckerboardSprite(cover_img,
                                        color1=Colour.LIGHT_GREEN, color2=Colour.DARK_GREEN,
                                        tile_size=self.tile,
                                        outline_color=Colour.LINE_GREEN,
                                        outline_thickness=line_width,
                                        batch=self.batch,
                                        group=Group(3, parent=self.group))

        # Cover highlight image
        self.light_green_hovered_tile = SolidColorImagePattern(Colour.LIGHT_GREEN_HOVER).create_image(self.tile,
                                                                                                      self.tile)
        self.dark_green_hovered_tile = SolidColorImagePattern(Colour.DARK_GREEN_HOVER).create_image(self.tile,
                                                                                                    self.tile)

        self.cover_highlight = Sprite(self.transparent_pattern,
                                      batch=self.batch,
                                      group=Group(4, parent=self.group))

        mines_layer_background_img = pyglet.image.Texture.create(width, height, blank_data=True)
        mines_layer_foreground_img = pyglet.image.Texture.create(width, height, blank_data=True)
        self.mines_layer = MinefieldSprite(mines_layer_background_img,
                                           mines_layer_foreground_img,
                                           tile_size=self.tile,
                                           batch=self.batch,
                                           group=Group(5, parent=self.group))

        self.particle_layer = Sprite(self.transparent_pattern,
                                     batch=self.batch,
                                     group=Group(6, parent=self.group))

        # Pyglet sprites
        self.number_labels: list[AbstractImage] = [pyglet.image.create(100, 100).get_image_data()]
        for n in range(1, 10):
            filename = f"{n}.png"
            with pyglet.resource.location(filename).open(filename) as image_file:
                self.number_labels.append(pyglet.image.load(filename=filename, file=image_file))

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
        self.number_layer.delete()
        self.mines_layer.delete()
        self.particle_layer.delete()

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

        # Create particle effect of tile disappearing
        particle = TileParticle(column * self.tile, row * self.tile,
                                self.tile, self.tile,
                                color=(Colour.DARK_GREEN, Colour.LIGHT_GREEN)[(row + column) % 2].to_rgb(),
                                batch=self.batch,
                                group=self.particle_layer.group)
        self.particles.append(particle)

        num = self.grid[row][column]
        if num == Minefield.MINE:
            color1, color2 = random.choice(MINE_COLOURS)

            mine_background_img = SolidColorImagePattern(
                color1,
            ).create_image(self.tile, self.tile)

            mine_foreground_img = SolidColorImagePattern(
                color2,
            ).create_image(self.tile, self.tile)

            self.mines_layer.images[0].blit_into(mine_background_img,
                                                 self.tile * column, self.tile * row, 0)

            self.mines_layer.images[1].blit_into(mine_foreground_img,
                                                 self.tile * column, self.tile * row, 0)

            self.dispatch_event("on_fail")
            return
        elif num > 0:
            # Add number label.
            self.number_layer.image.blit_into(self.number_labels[num],
                                              100 * column, 100 * row, 0)

        # Cut out the appropriate part of the cover image.
        self.cover.image.blit_into(self.transparent_pattern,
                                   self.tile * column,
                                   self.tile * row,
                                   0)

        # Remove flag in that position.
        if (row, column) in self.flags:
            self.flags.pop((row, column))
            self.dispatch_event("on_flag_remove", self)

    def uncover_all(self, diff: list[list[bool]]) -> int:
        iterations = 0
        for r in range(self.rows):
            for c in range(self.columns):
                if diff[r][c] and not self.revealed[r][c]:
                    self.uncover(r, c)
                    iterations += 1

        if iterations > 0 and not self.muted:
            # Sound effects
            if iterations == 1:
                clear_sfx.play()
            elif iterations > 1:
                flood_sfx.play()

        return iterations

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
            if iterations > 0:
                if not self.muted:
                    if self.grid[row][column] == 1:
                        one_reveal_sfx.play()
                    elif self.grid[row][column] == 2:
                        two_reveaL_sfx.play()
                    elif self.grid[row][column] == 3:
                        three_reveal_sfx.play()
                    elif self.grid[row][column] == 4:
                        four_reveal_sfx.play()

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
                if not self.muted:
                    flag_remove_sfx.play()
                self.dispatch_event("on_flag_remove", self)
            elif not self.revealed[row][column]:
                if not self.muted:
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
Checkerboard.register_event_type("on_fail")


class Game(Window):
    def __init__(self, difficulty: Difficulty, *, batch=None, group=None):
        self._difficulty = difficulty

        columns, rows, tile, mines, clear_start, line_width = DIFFICULTY_SETTINGS.get(self._difficulty)
        super().__init__(columns * tile, rows * tile + 60, caption="Google Minesweeeper")

        self.batch = batch or pyglet.graphics.get_default_batch()
        self.group = group or pyglet.graphics.get_default_group()

        # Checkerboard
        self.checkerboard = Checkerboard(0, 0, rows, columns, tile, mines, clear_start, line_width,
                                         muted=False, batch=self.batch, group=Group(0))

        # Tutorial
        self.tutorial = ui.Tutorial(self, self.width // 2, self.height // 2 + 45,
                                    batch=self.batch, group=self.group)

        # Header
        self.header = Rectangle(0, rows * tile, columns * tile, 60, color=Colour.HEADER_GREEN,
                                batch=self.batch, group=Group(3))

        self.counters = ui.Counters(self, difficulty, batch=self.batch, group=Group(4))

        self.mute_button = ui.MuteButton(self, batch=self.batch, group=Group(5))

        # Difficulty menu

        # self._difficulty
        self.diff_menu = ui.DifficultyMenu(self, difficulty, batch=self.batch, group=Group(6))

        # Event Handling
        self._setup_event_stack()

        # profile_uncover(self.checkerboard)

    def _setup_event_stack(self):
        self.push_handlers(self.checkerboard)

        self.push_handlers(self.diff_menu)
        self.push_handlers(self.diff_menu.button)
        self.push_handlers(self.diff_menu.dropdown)

        for child in self.diff_menu.dropdown.children:
            self.push_handlers(child)
            child.push_handlers(self)

        self.push_handlers(self.mute_button.button)

        self.mute_button.button.push_handlers(on_toggle=self.on_audio_toggle)

        # Event:
        # - self.mute_button.button =>
        # - self.diff_menu.dropdown.children =>
        # - self.diff_menu.dropdown =>
        # - self.diff_menu.button =>
        # - self.diff_menu =>
        # - self.checkerboard

        self.checkerboard.push_handlers(self)
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

        self.remove_handlers(self.mute_button.button)
        self.mute_button.button.remove_handlers(on_toggle=self.on_audio_toggle)

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

        # Mute Button
        self.mute_button.repack()

        # Difficulty Menu
        self.diff_menu.repack()

        # Checkerboard - recreate from scratch.
        self._remove_event_stack()

        muted = self.checkerboard.muted
        self.checkerboard.delete()
        del self.checkerboard

        self.checkerboard = Checkerboard(0, 0, rows, columns, tile, mines, clear_start, line_width,
                                         muted=muted, batch=self.batch, group=Group(0))
        self._setup_event_stack()

        self.tutorial.group.visible = False

    def on_draw(self):
        self.clear()
        self.batch.draw()

    def on_select(self, widget):
        difficulty = Difficulty(widget.label.text)
        self.difficulty = difficulty

    def on_audio_toggle(self, state):
        self.checkerboard.muted = state

    def on_fail(self):
        # The player has hit a mine.
        print("Mine hit!")


def profile_uncover(checkerboard):
    import cProfile, pstats
    from pstats import SortKey

    random.seed(3634)

    with cProfile.Profile() as pr:
        if checkerboard.grid.empty:
            checkerboard.grid.generate(checkerboard.mines)

        diff = create_grid(checkerboard.rows, checkerboard.columns, True)
        checkerboard.uncover_all(diff)

    with open("profile.txt", "w") as log:
        ps = pstats.Stats(pr, stream=log).strip_dirs()
        ps.sort_stats(SortKey.CUMULATIVE)
        ps.print_stats()


def main():
    game = Game(Difficulty.MEDIUM)

    if SHOW_FPS:
        fps_display = FPSDisplay(game)
        fps_display.label.color = Colour.BLACK

        def on_draw():
            game.clear()
            game.batch.draw()
            fps_display.draw()

        game.on_draw = on_draw

    pyglet.app.run()
