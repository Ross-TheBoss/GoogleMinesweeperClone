from collections import namedtuple
from enum import Enum


SHOW_FPS = False


class Difficulty(str, Enum):
    EASY = "Easy"
    BOSNIA = "Bosnia"
    MEDIUM = "Medium"
    HARD = "Hard"
    EXTREME = "Extreme"
    LOTTERY = "Lottery"
    BENCHMARK = "Benchmark"


DifficultySettingsTuple = namedtuple("DifficultySettingsTuple",
                                     ["columns", "rows", "tile", "mines",
                                      "guaranteed_start", "line_width"])
# Both columns and rows must be less than 328, due to the maximum texture size of 32,768px.
DIFFICULTY_SETTINGS = {
    Difficulty.EASY: DifficultySettingsTuple(10, 8, 45, 10, True, 4),
    Difficulty.BOSNIA: DifficultySettingsTuple(10, 10, 45, 50, True, 2),
    Difficulty.MEDIUM: DifficultySettingsTuple(18, 14, 30, 40, True, 2),
    Difficulty.HARD: DifficultySettingsTuple(24, 20, 25, 99, True, 2),
    Difficulty.EXTREME: DifficultySettingsTuple(38, 30, 20, 300, True, 1),
    Difficulty.LOTTERY: DifficultySettingsTuple(5, 5, 100, 24, False, 8),
    Difficulty.BENCHMARK: DifficultySettingsTuple(152, 120, 5, 4000, True, 1),
}


class Colour(tuple, Enum):
    RGBA = tuple[int, int, int, int]

    def to_rgb(self) -> tuple[int, int, int]:
        return self[0], self[1], self[2]

    def with_alpha(self, alpha) -> RGBA:
        return self[0], self[1], self[2], alpha

    LIGHT_BLUE: RGBA = (143, 202, 249, 0)
    DARK_BLUE: RGBA = (133, 197, 247, 0)

    LIGHT_GREEN: RGBA = (170, 215, 81, 255)
    LIGHT_GREEN_HOVER: RGBA = (191, 225, 125, 255)

    DARK_GREEN: RGBA = (162, 209, 73, 255)
    DARK_GREEN_HOVER: RGBA = (185, 221, 119, 255)

    LINE_GREEN: RGBA = (135, 175, 58, 255)

    HEADER_GREEN: RGBA = (74, 117, 44, 255)

    LIGHT_BROWN: RGBA = (229, 194, 159, 255)
    LIGHT_BROWN_HOVER: RGBA = (236, 209, 183, 255)

    DARK_BROWN: RGBA = (215, 184, 153, 255)
    DARK_BROWN_HOVER: RGBA = (225, 202, 179, 255)

    DIFFICULTY_SELECTED: RGBA = (229, 229, 229, 255)

    TRANSPARENT: RGBA = (0, 0, 0, 0)
    ONE: RGBA = (25, 118, 210, 255)
    TWO: RGBA = (56, 142, 60, 255)
    THREE: RGBA = (211, 47, 47, 255)
    FOUR: RGBA = (123, 31, 162, 255)
    FIVE: RGBA = (255, 143, 0, 255)
    SIX: RGBA = (0, 151, 167, 255)
    SEVEN: RGBA = (66, 66, 66, 255)
    EIGHT: RGBA = (158, 158, 158, 255)

    DIFFICULTY_LABEL: RGBA = (48, 48, 48, 255)

    MODAL_BACKDROP_BLACK = (0, 0, 0, 179)
    SKY_BLUE = (77, 193, 249, 255)
    CLEARED_GREEN = (211, 233, 162, 255)

    WHITE: RGBA = (255, 255, 255, 255)
    BLACK: RGBA = (0, 0, 0, 255)

    MINE_GREEN: RGBA = (0, 132, 65, 255)
    MINE_YELLOW: RGBA = (238, 188, 11, 255)
    MINE_BLUE: RGBA = (71, 130, 231, 255)
    MINE_PURPLE: RGBA = (178, 70, 237, 255)
    MINE_PINK: RGBA = (231, 66, 177, 255)
    MINE_CYAN: RGBA = (71, 225, 237, 255)
    MINE_RED: RGBA = (213, 48, 52, 255)
    MINE_ORANGE: RGBA = (240, 128, 10, 255)

    MINE_DARK_GREEN: RGBA = (0, 86, 41, 255)
    MINE_DARK_YELLOW: RGBA = (155, 122, 8, 255)
    MINE_DARK_BLUE: RGBA = (44, 84, 150, 255)
    MINE_DARK_PURPLE: RGBA = (117, 46, 153, 255)
    MINE_DARK_PINK: RGBA = (150, 43, 115, 255)
    MINE_DARK_CYAN: RGBA = (47, 146, 153, 255)
    MINE_DARK_RED: RGBA = (139, 32, 33, 255)
    MINE_DARK_ORANGE: RGBA = (155, 83, 6, 255)


NUM_COLOURS = (Colour.TRANSPARENT,
               Colour.ONE,
               Colour.TWO,
               Colour.THREE,
               Colour.FOUR,
               Colour.FIVE,
               Colour.SIX,
               Colour.SEVEN,
               Colour.EIGHT)

MINE_COLOURS = ((Colour.MINE_GREEN, Colour.MINE_DARK_GREEN),
                (Colour.MINE_YELLOW, Colour.MINE_DARK_YELLOW),
                (Colour.MINE_BLUE, Colour.MINE_DARK_BLUE),
                (Colour.MINE_PURPLE, Colour.MINE_DARK_PURPLE),
                (Colour.MINE_PINK, Colour.MINE_DARK_PINK),
                (Colour.MINE_CYAN, Colour.MINE_DARK_CYAN),
                (Colour.MINE_RED, Colour.MINE_DARK_RED),
                (Colour.MINE_ORANGE, Colour.MINE_DARK_ORANGE))


class Ordinal(tuple, Enum):
    NORTH = (1, 0)
    NORTH_EAST = (1, -1)
    EAST = (0, -1)
    SOUTH_EAST = (-1, -1)
    SOUTH = (-1, 0)
    SOUTH_WEST = (-1, 1)
    WEST = (0, 1)
    NORTH_WEST = (1, 1)
