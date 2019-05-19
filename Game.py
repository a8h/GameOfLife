import random
import sys
import time
import curses
from curses import wrapper
import locale
import logging

"""
The universe of the Game of Life is an infinite, two-dimensional orthogonal grid of square cells, each of which is in one of two possible states, alive or dead, (or populated and unpopulated, respectively). 
Every cell interacts with its eight neighbours, which are the cells that are horizontally, vertically, or diagonally adjacent.
At each step in time, the following transitions occur:

    Any live cell with fewer than two live neighbours dies, as if by underpopulation.
    Any live cell with two or three live neighbours lives on to the next generation.
    Any live cell with more than three live neighbours dies, as if by overpopulation.
    Any dead cell with exactly three live neighbours becomes a live cell, as if by reproduction.
    The initial pattern constitutes the seed of the system.
    The first generation is created by applying the above rules simultaneously to every cell in the seed; births and deaths occur simultaneously, and the discrete moment at which this happens is sometimes called a tick. 
    Each generation is a pure function of the preceding one.
    The rules continue to be applied repeatedly to create further generations.

"""

locale.setlocale(locale.LC_ALL, '')
code = locale.getpreferredencoding()

def rand_init_grid(num_rows, num_cols, with_border = False):
    # A grid with 0s on the outsides and random 0s or 1s in the inside
    if with_border:
        return [[random.randint(0,1) if i > 0 and i < num_cols - 1 else 0 for i in xrange(num_cols)] if i > 0 and i < num_rows - 1 else [0] * num_cols for i in xrange(num_rows)]
    else:
        return [[random.randint(0,1) for i in range(num_cols)] for i in range(num_rows)]
    
def printGrid(grid, symbol_live = u'\u2584', symbol_dead = ' '):
    return '\n'.join([' '.join([symbol_live.encode('UTF-8') if i else symbol_dead.encode('UTF-8') for i in list]) for list in grid])

#Assuming grids are rectangular
def state_transition(current_grid, future_grid):
    for row_num in xrange(len(current_grid[:])):
        for col_num in xrange(len(current_grid[0][:])):
            future_grid[row_num][col_num] = cell_transition(row_num, col_num, current_grid)

def cell_transition(row_num, col_num, grid):
    live_count = live_neighbor_count(row_num, col_num, grid)
    alive = grid[row_num][col_num]
    #Any live cell with fewer than two live neighbours dies, as if by underpopulation.
    if alive and live_count < 2:
        return 0

    #Any live cell with two or three live neighbours lives on to the next generation.
    elif alive and live_count == 2 or live_count == 3:
        return 1

    #Any live cell with more than three live neighbours dies, as if by overpopulation.
    elif alive and live_count > 3:
        return 0

    #Any dead cell with exactly three live neighbours becomes a live cell, as if by reproduction.
    elif not alive and live_count == 3:
        return 1
    else:
        return alive

# Naive way
def live_neighbor_count(row_num, col_num, grid):
    count = 0
    wrap_vertical, wrap_horizontal = len(grid), len(grid[0])

    #Top left
    if grid[(row_num - 1) % wrap_vertical][(col_num - 1) % wrap_horizontal]:
        count += 1
    #Top middle
    if grid[(row_num - 1) % wrap_vertical][col_num]:
        count += 1
    #Top right
    if grid[(row_num - 1) % wrap_vertical][(col_num + 1) % wrap_horizontal]:
        count += 1

    #Bottom right
    if grid[(row_num + 1) % wrap_vertical][(col_num - 1) % wrap_horizontal]:
        count += 1
    #Bottom middle
    if grid[(row_num + 1) % wrap_vertical][col_num]:
        count += 1
    #Bottom right
    if grid[(row_num + 1) % wrap_vertical][(col_num + 1) % wrap_horizontal]:
        count += 1

    #Middle left
    if grid[row_num % wrap_vertical][(col_num - 1) % wrap_horizontal]:
        count += 1

    #Middle right
    if grid[row_num % wrap_vertical][(col_num + 1) % wrap_horizontal]:
        count += 1

    return count

def init_game():
    try:
        rows = int(sys.argv[1])
        cols = int(sys.argv[2])
        steps = int(sys.argv[3])
        refresh_time = float(sys.argv[4])

    #Add some default values
    except IndexError as e:
        steps = 1000
        refresh_time = 0.04

    grid_1 = rand_init_grid(rows,cols)
    grid_2 = [[0 for i in range(cols)] for i in range(rows)]
    return (grid_1, grid_2, steps, refresh_time)

def run_game(stdscr):
    stdscr.clear()
    grid_1, grid_2, steps, refresh_time = init_game()

    curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)
    stdscr.addstr(0,0, printGrid(grid_1), curses.color_pair(1))
    stdscr.refresh()
    time.sleep(refresh_time)

    for x in xrange(steps):
        if x % 2 == 0:
            state_transition(grid_1, grid_2)
            stdscr.addstr(0,0, printGrid(grid_2), curses.color_pair(1))
            stdscr.refresh()
            time.sleep(refresh_time)

        else:
            state_transition(grid_2, grid_1)
            stdscr.addstr(0,0, printGrid(grid_1), curses.color_pair(1))
            stdscr.refresh()
            time.sleep(refresh_time)
    stdscr.refresh()
    stdscr.getkey()

def main(stdscr):
    run_game(stdscr)

wrapper(main)

def tests():
    pass
    #run_game(5)
    #input = [[1,1,1],[1,1,1],[1,1,1]]
    #print(printGrid(input, '1', '0'))
    # arr = rand_init_grid(10,10)
    # printGrid(input)
    # print(live_neighbor_count(1,1,input))
    #print(printGrid(rand_init_grid(6,6)))
#tests()
