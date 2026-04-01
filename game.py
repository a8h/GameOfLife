"""
Conway's Game of Life:
https://en.wikipedia.org/wiki/Conway%27s_Game_of_Life#Rules
"""

import random
import sys
import time
import curses
from curses import wrapper
import locale
from typing import Union

try:
    range_compat = xrange
except NameError:
    range_compat = range

locale.setlocale(locale.LC_ALL, '')
locale.getpreferredencoding()

ESC_KEY = 27
ESC_DELAY_MS = 1
EXIT_KEYS = (ord('q'), ord('Q'), ESC_KEY)
DEFAULT_FOREGROUND_COLOR = 'green'
DEFAULT_BACKGROUND_COLOR = 'black'
COLOR_NAME_TO_CURSES = {
    'black': curses.COLOR_BLACK,
    'blue': curses.COLOR_BLUE,
    'cyan': curses.COLOR_CYAN,
    'green': curses.COLOR_GREEN,
    'magenta': curses.COLOR_MAGENTA,
    'red': curses.COLOR_RED,
    'white': curses.COLOR_WHITE,
    'yellow': curses.COLOR_YELLOW,
}
MAX_EXTENDED_COLOR = 255
RESTART_DELAY_SECONDS = 1
ColorValue = Union[int, str]


def rand_init_grid(
    num_rows: int, num_cols: int, with_border: bool = False
) -> list[list[int]]:
    """ Initialize a grid randomly with 0s and 1s.

    Args:
        num_rows (int): Number of rows in the grid.
        num_cols (int): Number of columns in the grid.
        with_border (bool): Whether to border the grid with 0s.

    Returns:
        list: A 2-D grid represented by a list of lists.

    """
    num_rows, num_cols = int(num_rows), int(num_cols)
    if with_border:
        return [[
            random.randint(0, 1) if col_index > 0 and col_index < num_cols - 1 else 0
            for col_index in range_compat(num_cols)
        ] if row_index > 0 and row_index < num_rows - 1 else [0] * num_cols
            for row_index in range_compat(num_rows)]
    return [[random.randint(0, 1) for _ in range_compat(num_cols)] for _ in range_compat(num_rows)]

def print_grid(
    grid: list[list[int]], symbol_live: str = u'\u2584', symbol_dead: str = ' '
) -> bytes:
    """ Create a string byte representation of the grid.

    Args:
        grid (list): A 2-d grid represented by a list of lists.
        symbol_live(str): The symbol used to represent live cells.
        symbol_dead(str): The symbol used to represent dead cells.

    Returns:
        bytes: A string of bytes representing the grid.

    """
    return b'\n'.join([b' '.join([
        symbol_live.encode('UTF-8') if cell else symbol_dead.encode('UTF-8')
        for cell in row
    ]) for row in grid])


def make_grids(num_rows: int, num_cols: int) -> tuple[list[list[int]], list[list[int]]]:
    """Create the current grid and an empty future grid."""
    current_grid = rand_init_grid(num_rows, num_cols)
    future_grid = [[0 for _ in range_compat(num_cols)] for _ in range_compat(num_rows)]
    return current_grid, future_grid


def grid_signature(grid: list[list[int]]) -> tuple[tuple[int, ...], ...]:
    """Create a hashable signature for a grid state."""
    return tuple(tuple(row) for row in grid)


def is_repeated_state(
    seen_states: set[tuple[tuple[int, ...], ...]],
    grid: list[list[int]],
) -> bool:
    """Report whether a grid state has already been seen."""
    return grid_signature(grid) in seen_states


def record_state(seen_states: set[tuple[tuple[int, ...], ...]], grid: list[list[int]]) -> None:
    """Record a grid state in the seen-state set."""
    seen_states.add(grid_signature(grid))


def restart_grids(num_rows: int, num_cols: int) -> tuple[list[list[int]], list[list[int]]]:
    """Pause briefly before restarting with a fresh random grid."""
    time.sleep(RESTART_DELAY_SECONDS)
    return make_grids(num_rows, num_cols)

# Assuming grids are rectangular
def state_transition(
    current_grid: list[list[int]],
    future_grid: list[list[int]],
    with_border: bool = False,
) -> None:
    """ Transition between grids.

    Args:
        current_grid (list): The 2-d grid representation of the current state of the simulation.
        future_grid (list): The 2-d grid that will store the representation of the next state \
                of the simulation.
        with_border (bool): Whether to preserve a dead border around the grid.

    Returns:
        None

    """
    row_start = 1 if with_border else 0
    row_end = len(current_grid) - 1 if with_border else len(current_grid)
    col_start = 1 if with_border else 0
    col_end = len(current_grid[0]) - 1 if with_border else len(current_grid[0])

    if with_border:
        for row_num in range_compat(len(current_grid)):
            future_grid[row_num][0] = 0
            future_grid[row_num][-1] = 0
        for col_num in range_compat(len(current_grid[0])):
            future_grid[0][col_num] = 0
            future_grid[-1][col_num] = 0

    for row_num in range_compat(row_start, row_end):
        for col_num in range_compat(col_start, col_end):
            future_grid[row_num][col_num] = cell_transition(row_num, col_num, current_grid)

def cell_transition(row_num: int, col_num: int, grid: list[list[int]]) -> int:
    """ Uses Conway's rules to determine whether a cell should live (1) or die (0).

    Args:
        row_num (int): The row position of the cell.
        col_num (int): The column position of the cell.
        grid (list): A 2-d grid represented by a list of lists.

    Returns:
        int: 1 for alive. 0 for dead.

    """
    live_count = live_neighbor_count(row_num, col_num, grid)
    living_status = grid[row_num][col_num]

    # Any live cell with fewer than two live neighbours dies, as if by underpopulation.
    if living_status and live_count < 2:
        return 0

    # Any live cell with two or three live neighbours lives on to the next generation.
    elif living_status and live_count == 2 or live_count == 3:
        return 1

    # Any live cell with more than three live neighbours dies, as if by overpopulation.
    elif living_status and live_count > 3:
        return 0

    # Any dead cell with exactly three live neighbours becomes a live cell, as if by reproduction.
    elif not living_status and live_count == 3:
        return 1
    return living_status

# Naive way
def live_neighbor_count(row_num: int, col_num: int, grid: list[list[int]]) -> int:
    """ Compute how many of the eight neighboring cells are alive.

    Args:
        row_num (int): The row position of the cell.
        col_num (int): The column position of the cell.
        grid (list): A 2-d grid represented by a list of lists.

    Returns:
        int: Number of neighboring cells that are alive.

    """
    count = 0
    wrap_vertical, wrap_horizontal = len(grid), len(grid[0])

    # Top left
    if grid[(row_num - 1) % wrap_vertical][(col_num - 1) % wrap_horizontal]:
        count += 1
    # Top middle
    if grid[(row_num - 1) % wrap_vertical][col_num]:
        count += 1
    # Top right
    if grid[(row_num - 1) % wrap_vertical][(col_num + 1) % wrap_horizontal]:
        count += 1

    # Bottom right
    if grid[(row_num + 1) % wrap_vertical][(col_num - 1) % wrap_horizontal]:
        count += 1
    # Bottom middle
    if grid[(row_num + 1) % wrap_vertical][col_num]:
        count += 1
    # Bottom right
    if grid[(row_num + 1) % wrap_vertical][(col_num + 1) % wrap_horizontal]:
        count += 1

    # Middle left
    if grid[row_num % wrap_vertical][(col_num - 1) % wrap_horizontal]:
        count += 1
    # Middle right
    if grid[row_num % wrap_vertical][(col_num + 1) % wrap_horizontal]:
        count += 1

    return count

def init_game(
    stdscr: curses.window,
) -> tuple[list[list[int]], list[list[int]], int, float, ColorValue, ColorValue]:
    """ Initialize the game and values for ncurses.

    Args:
        stdscr (WindowObject): A representation of the screen provided by ncurses' wrapper.

    Returns:
        tuple: A tuple containing the initialized values for the game.

    """
    rows, cols = stdscr.getmaxyx()
    cols /= 2
    steps = sys.maxsize
    refresh_time = 0.04
    foreground_color = DEFAULT_FOREGROUND_COLOR
    background_color = DEFAULT_BACKGROUND_COLOR

    if len(sys.argv) > 1:
        rows = int(sys.argv[1])
    if len(sys.argv) > 2:
        cols = int(sys.argv[2])
    if len(sys.argv) > 3:
        steps = int(sys.argv[3])
    if len(sys.argv) > 4:
        refresh_time = float(sys.argv[4])
    if len(sys.argv) > 5:
        foreground_color = parse_color(sys.argv[5])
    if len(sys.argv) > 6:
        background_color = parse_color(sys.argv[6])

    rows, cols = int(rows), int(cols)
    grid_1, grid_2 = make_grids(rows, cols)
    return (
        grid_1,
        grid_2,
        steps,
        refresh_time,
        foreground_color,
        background_color,
    )


def parse_color(color_name: str) -> ColorValue:
    """Normalize and validate a terminal color name or palette index."""
    normalized_color = color_name.lower()
    if normalized_color.isdigit():
        color_number = int(normalized_color)
        if color_number > MAX_EXTENDED_COLOR:
            raise ValueError('Color index out of range: {}'.format(color_name))
        return color_number
    if normalized_color not in COLOR_NAME_TO_CURSES:
        raise ValueError('Unsupported color: {}'.format(color_name))
    return normalized_color


def resolve_curses_color(color: ColorValue) -> int:
    """Resolve a named or numeric color value to a curses color number."""
    if isinstance(color, int):
        supported_color_count = getattr(curses, 'COLORS', len(COLOR_NAME_TO_CURSES))
        if color >= supported_color_count:
            raise ValueError('Terminal does not support color {}'.format(color))
        return color
    return COLOR_NAME_TO_CURSES[color]


def configure_colors(foreground_color: ColorValue, background_color: ColorValue) -> int:
    """Initialize curses colors and return the pair used for rendering."""
    curses.start_color()
    foreground = resolve_curses_color(foreground_color)
    background = resolve_curses_color(background_color)
    curses.init_pair(
        1,
        foreground,
        background,
    )
    return curses.color_pair(1)


def should_exit(key_pressed: int) -> bool:
    """Return whether the pressed key should exit the game."""
    return key_pressed in EXIT_KEYS


def configure_input(stdscr: curses.window, refresh_time: float) -> None:
    """Configure keyboard input timing for the game loop."""
    curses.set_escdelay(ESC_DELAY_MS)
    stdscr.timeout(int(refresh_time * 1000))

def run_game(stdscr: curses.window) -> None:
    """ Runs the main game loop.

    Args:
        stdscr (WindowObject): A representation of the screen provided by ncurses' wrapper.

    Returns:
        None

    """
    try:
        stdscr.clear()
        (
            grid_1,
            grid_2,
            steps,
            refresh_time,
            foreground_color,
            background_color,
        ) = init_game(stdscr)
        curses.curs_set(0)
        color_pair = configure_colors(foreground_color, background_color)
        configure_input(stdscr, refresh_time)
        current_grid, future_grid = grid_1, grid_2
        seen_states = set()
        record_state(seen_states, current_grid)

        stdscr.addstr(0, 0, print_grid(current_grid), color_pair)
        stdscr.refresh()

        for _ in range_compat(steps):
            if should_exit(stdscr.getch()):
                break
            state_transition(current_grid, future_grid)
            if is_repeated_state(seen_states, future_grid):
                current_grid, future_grid = restart_grids(
                    len(current_grid),
                    len(current_grid[0]),
                )
                seen_states = set()
                record_state(seen_states, current_grid)
            else:
                record_state(seen_states, future_grid)
                current_grid, future_grid = future_grid, current_grid
            stdscr.addstr(0, 0, print_grid(current_grid), color_pair)
            stdscr.refresh()
    except KeyboardInterrupt:
        pass

if __name__ == '__main__':
    wrapper(run_game)
