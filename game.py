"""
Conway's Game of Life:
https://en.wikipedia.org/wiki/Conway%27s_Game_of_Life#Rules
"""

import random
import sys
import time
import argparse
import curses
import os
import subprocess
import traceback
from collections import deque
from curses import wrapper
import locale
from typing import Deque, Optional, Union

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
MEMORY_LOG_INTERVAL_SECONDS = 1
MAX_TRACKED_STATES = 5
DEBUG_LOG_PATH = os.path.join(os.path.dirname(__file__), 'game_debug.log')
ColorValue = Union[int, str]
StateSignature = tuple[tuple[int, ...], ...]


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


def grid_signature(grid: list[list[int]]) -> StateSignature:
    """Create a hashable signature for a grid state."""
    return tuple(tuple(row) for row in grid)


def is_repeated_state(
    recent_states: Deque[StateSignature],
    grid: list[list[int]],
) -> bool:
    """Report whether a grid state has already been seen."""
    return grid_signature(grid) in recent_states


def record_state(recent_states: Deque[StateSignature], grid: list[list[int]]) -> None:
    """Record a grid state in the bounded recent-state history."""
    recent_states.append(grid_signature(grid))


def restart_grids(num_rows: int, num_cols: int) -> tuple[list[list[int]], list[list[int]]]:
    """Pause briefly before restarting with a fresh random grid."""
    time.sleep(RESTART_DELAY_SECONDS)
    return make_grids(num_rows, num_cols)


def append_debug_log(message: str, log_path: str = DEBUG_LOG_PATH) -> None:
    """Append a debug message to the log file."""
    with open(log_path, 'a') as debug_log:
        debug_log.write(message + '\n')


def current_timestamp() -> str:
    """Return the current wall-clock timestamp for debug logging."""
    return time.strftime('%Y-%m-%dT%H:%M:%S')


def get_memory_usage_kb() -> int:
    """Return the current process resident set size in kilobytes."""
    output = subprocess.check_output(
        ['ps', '-o', 'rss=', '-p', str(os.getpid())],
        universal_newlines=True,
    )
    return int(output.strip())


def log_memory_usage(
    last_logged_at: float,
    tracked_state_count: int,
    log_path: str = DEBUG_LOG_PATH,
    current_time: Optional[float] = None,
) -> float:
    """Write a periodic memory usage sample to the debug log."""
    current_time = time.monotonic() if current_time is None else current_time
    if current_time - last_logged_at < MEMORY_LOG_INTERVAL_SECONDS:
        return last_logged_at
    try:
        append_debug_log(
            '[{}] rss_kb={} tracked_states={}'.format(
                current_timestamp(),
                get_memory_usage_kb(),
                tracked_state_count,
            ),
            log_path,
        )
    except Exception:
        append_debug_log(
            '[{}] memory_log_failed {}'.format(
                current_timestamp(),
                traceback.format_exc().rstrip().replace('\n', ' | '),
            ),
            log_path,
        )
    return current_time


def log_unhandled_exception(log_path: str = DEBUG_LOG_PATH) -> None:
    """Write the active exception traceback to the debug log."""
    append_debug_log(
        '[{}] unhandled_exception\n{}'.format(
            current_timestamp(),
            traceback.format_exc().rstrip(),
        ),
        log_path,
    )

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
    rows, cols, steps, refresh_time, foreground_color, background_color = parse_cli_arguments(
        int(rows),
        int(cols / 2),
    )
    grid_1, grid_2 = make_grids(rows, cols)
    return (
        grid_1,
        grid_2,
        steps,
        refresh_time,
        foreground_color,
        background_color,
    )


def choose_argument(
    positional_value: Optional[ColorValue],
    option_value: Optional[ColorValue],
    default_value: ColorValue,
) -> ColorValue:
    """Prefer a named option, then a positional argument, then the default."""
    if option_value is not None:
        return option_value
    if positional_value is not None:
        return positional_value
    return default_value


def parse_cli_arguments(
    default_rows: int,
    default_cols: int,
    argv: Optional[list[str]] = None,
) -> tuple[int, int, int, float, ColorValue, ColorValue]:
    """Parse positional and named CLI arguments for the game."""
    parser = argparse.ArgumentParser()
    parser.add_argument('rows', nargs='?', type=int)
    parser.add_argument('cols', nargs='?', type=int)
    parser.add_argument('steps', nargs='?', type=int)
    parser.add_argument('delay', nargs='?', type=float)
    parser.add_argument('foreground_color', nargs='?', type=parse_color)
    parser.add_argument('background_color', nargs='?', type=parse_color)
    parser.add_argument('--rows', dest='rows_option', type=int)
    parser.add_argument('--cols', dest='cols_option', type=int)
    parser.add_argument('--steps', dest='steps_option', type=int)
    parser.add_argument('--delay', dest='delay_option', type=float)
    parser.add_argument('--fg', dest='foreground_color_option', type=parse_color)
    parser.add_argument('--bg', dest='background_color_option', type=parse_color)

    parsed_arguments = parser.parse_args(sys.argv[1:] if argv is None else argv)
    rows = choose_argument(parsed_arguments.rows, parsed_arguments.rows_option, default_rows)
    cols = choose_argument(parsed_arguments.cols, parsed_arguments.cols_option, default_cols)
    steps = choose_argument(parsed_arguments.steps, parsed_arguments.steps_option, sys.maxsize)
    refresh_time = choose_argument(parsed_arguments.delay, parsed_arguments.delay_option, 0.04)
    foreground_color = choose_argument(
        parsed_arguments.foreground_color,
        parsed_arguments.foreground_color_option,
        DEFAULT_FOREGROUND_COLOR,
    )
    background_color = choose_argument(
        parsed_arguments.background_color,
        parsed_arguments.background_color_option,
        DEFAULT_BACKGROUND_COLOR,
    )
    return (
        int(rows),
        int(cols),
        int(steps),
        float(refresh_time),
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
        recent_states: Deque[StateSignature] = deque(maxlen=MAX_TRACKED_STATES)
        record_state(recent_states, current_grid)
        last_memory_log_at = 0.0

        append_debug_log(
            '[{}] session_start pid={} rows={} cols={} refresh_time={}'.format(
                current_timestamp(),
                os.getpid(),
                len(current_grid),
                len(current_grid[0]),
                refresh_time,
            ),
        )
        last_memory_log_at = log_memory_usage(last_memory_log_at, len(recent_states))

        stdscr.addstr(0, 0, print_grid(current_grid), color_pair)
        stdscr.refresh()

        for _ in range_compat(steps):
            if should_exit(stdscr.getch()):
                break
            state_transition(current_grid, future_grid)
            if is_repeated_state(recent_states, future_grid):
                current_grid, future_grid = restart_grids(
                    len(current_grid),
                    len(current_grid[0]),
                )
                recent_states = deque(maxlen=MAX_TRACKED_STATES)
                record_state(recent_states, current_grid)
            else:
                record_state(recent_states, future_grid)
                current_grid, future_grid = future_grid, current_grid
            last_memory_log_at = log_memory_usage(last_memory_log_at, len(recent_states))
            stdscr.addstr(0, 0, print_grid(current_grid), color_pair)
            stdscr.refresh()
    except KeyboardInterrupt:
        pass
    except Exception:
        log_unhandled_exception()
        raise

if __name__ == '__main__':
    wrapper(run_game)
