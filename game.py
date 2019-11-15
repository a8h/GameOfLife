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

locale.setlocale(locale.LC_ALL, '')
locale.getpreferredencoding()


def rand_init_grid(num_rows, num_cols, with_border=False):
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
        return [[random.randint(0, 1) if i > 0 and i < num_cols - 1 else 0 \
            for i in xrange(num_cols)] if i > 0 and i < num_rows - 1 \
            else [0] * num_cols for i in xrange(num_rows)]
    return [[random.randint(0, 1) for i in xrange(num_cols)] for i in xrange(num_rows)]

def print_grid(grid, symbol_live=u'\u2584', symbol_dead=' '):
    """ Create a string byte representation of the grid.

    Args:
        grid (list): A 2-d grid represented by a list of lists.
        symbol_live(str): The symbol used to represent live cells.
        symbol_dead(str): The symbol used to represent dead cells.

    Returns:
        bytes: A string of bytes representing the grid.

    """
    return b'\n'.join([b' '.join([symbol_live.encode('UTF-8') if i \
            else symbol_dead.encode('UTF-8') for i in arr]) for arr in grid])

# Assuming grids are rectangular
def state_transition(current_grid, future_grid):
    """ Transition between grids.

    Args:
        current_grid (list): The 2-d grid representation of the current state of the simulation.
        future_grid (list): The 2-d grid that will store the representation of the next state \
                of the simulation.

    Returns:
        None

    """
    for row_num in xrange(len(current_grid[:])):
        for col_num in xrange(len(current_grid[0][:])):
            future_grid[row_num][col_num] = cell_transition(row_num, col_num, current_grid)

def cell_transition(row_num, col_num, grid):
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
def live_neighbor_count(row_num, col_num, grid):
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

def init_game(stdscr):
    """ Initialize the game and values for ncurses.

    Args:
        stdscr (WindowObject): A representation of the screen provided by ncurses' wrapper.

    Returns:
        tuple: A tuple containing the initialized values for the game.

    """
    try:
        rows = int(sys.argv[1])
        cols = int(sys.argv[2])
        steps = int(sys.argv[3])
        refresh_time = float(sys.argv[4])

    # Default values
    except IndexError:
        rows, cols = stdscr.getmaxyx()
        cols /= 2
        steps = sys.maxsize
        refresh_time = 0.04

    rows, cols = int(rows), int(cols)
    grid_1 = rand_init_grid(rows, cols)
    grid_2 = [[0 for _ in xrange(cols)] for _ in xrange(rows)]
    return (grid_1, grid_2, steps, refresh_time)

def run_game(stdscr):
    """ Runs the main game loop.

    Args:
        stdscr (WindowObject): A representation of the screen provided by ncurses' wrapper.

    Returns:
        None

    """
    try:
        stdscr.clear()
        grid_1, grid_2, steps, refresh_time = init_game(stdscr)
        curses.curs_set(0)
        curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)
        stdscr.addstr(0, 0, print_grid(grid_1), curses.color_pair(1))
        stdscr.refresh()
        time.sleep(refresh_time)

        for step in xrange(steps):
            if step % 2:
                state_transition(grid_2, grid_1)
                stdscr.addstr(0, 0, print_grid(grid_1), curses.color_pair(1))
            else:
                state_transition(grid_1, grid_2)
                stdscr.addstr(0, 0, print_grid(grid_2), curses.color_pair(1))
            stdscr.refresh()
            time.sleep(refresh_time)
    except KeyboardInterrupt:
        pass

if __name__ == '__main__':
    # For quick Python3 compatibility
    try:
        xrange
    except NameError:
        xrange = range
    wrapper(run_game)
