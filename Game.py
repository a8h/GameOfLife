import random
import sys
import time
import curses
from curses import wrapper
import locale

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

# A grid with 0s on the outsides and random 0s or 1s in the inside
def rand_init_grid(num_rows, num_cols):
    return [[random.randint(0,1) if i > 0 and i < num_cols - 1 else 0 for i in xrange(num_cols)] if i > 0 and i < num_rows - 1 else [0] * num_cols for i in xrange(num_rows)]
    
def printGridInts(grid):
    return '\n'.join([' '.join([u'\u2584'.encode('UTF-8') if i else ' ' for i in list]) for list in grid])

def withinGrid(row_num, col_num, grid):
    return (row_num > 0 and row_num < len(grid[0]) - 1) and (col_num > 0 and col_num < len(grid) - 1)

#Assuming grids are rectangular and edges are not included
def state_transition(current_grid, future_grid):
    for row_num in xrange(len(current_grid[1:-1])):
        row_num += 1
        for col_num in xrange(len(current_grid[0][1:-1])):
            col_num += 1
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
    #Count top row
    for x in grid[row_num - 1][col_num - 1: col_num + 2]:
        if x:
            count += 1

    #Count bottom row
    for x in grid[row_num + 1][col_num - 1: col_num + 2]:
        if x:
            count += 1

    if grid[row_num][col_num - 1]:
        count += 1

    if grid[row_num][col_num + 1]:
        count += 1

    return count

def init_game():
    rows = int(sys.argv[1])
    cols = int(sys.argv[2])
    steps = int(sys.argv[3])
    refresh_time = float(sys.argv[4])

    grid_1 = rand_init_grid(rows,cols)
    grid_2 = [[0 for i in range(cols)] for i in range(rows)]
    return (grid_1, grid_2, steps, refresh_time)

def run_game(stdscr):
    stdscr.clear()
    grid_1, grid_2, steps, refresh_time = init_game()

    curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)
    stdscr.addstr(0,0, printGridInts(grid_2), curses.color_pair(1))
    stdscr.refresh()
    time.sleep(refresh_time)
    stdscr.addstr(0,0, printGridInts(grid_1), curses.color_pair(1))
    stdscr.refresh()
    time.sleep(refresh_time)

    for x in xrange(steps):
        if x % 2 == 0:
            state_transition(grid_1, grid_2)
            stdscr.addstr(0,0, printGridInts(grid_2), curses.color_pair(1))
            stdscr.refresh()
            time.sleep(refresh_time)

        else:
            state_transition(grid_2, grid_1)
            stdscr.addstr(0,0, printGridInts(grid_1), curses.color_pair(1))
            stdscr.refresh()
            time.sleep(refresh_time)
    stdscr.refresh()
    stdscr.getkey()

def main(stdscr):
    run_game(stdscr)

wrapper(main)

def tests():
    #run_game(5)

    input = [[1,1,1],[1,1,1],[1,1,1]]
    print(printGridInts(input))

    # printGridInts(input)
    # print(withinGrid(1,1,input))
    # print(withinGrid(0,1,input))
    # print(withinGrid(2,1,input))
    # print(live_neighbor_count(1,1,input))
    #print(printGridInts(rand_init_grid(6,6)))
