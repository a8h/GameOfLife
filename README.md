# Conway's Game of Life
Visualizing Conway's Game of Life on the terminal.

## Example
A screenshot of the visualization:

![Game of Life Visualization](example.png)

## Requirements
* Python 2.7 or Python 3.5
* Unix-based OS (for ncurses support)

## Usage
Run the Game of Life visualization with default settings (grid size equals size of the terminal window):

`$ python game.py`

Create a 24 x 40 block grid on your terminal, and run for 1000 ticks with a pause of 0.04 seconds between each tick:

`$ python game.py 24 40 1000 0.04`

Create a 24 x 40 block grid with red live cells on a black background:

`$ python game.py 24 40 1000 0.04 red black`

Create a 24 x 40 block grid with 256-color palette values:

`$ python game.py 24 40 1000 0.04 196 234`

Named options let you skip `steps` while still setting later arguments:

`$ python3 game.py 24 40 --delay 0.04 --fg 111 --bg 11`

You can also use named options for any of the positional values:

`$ python3 game.py --rows 24 --cols 40 --steps 1000 --delay 0.04 --fg red --bg black`

Supported colors: named colors `black`, `blue`, `cyan`, `green`, `magenta`, `red`, `white`, `yellow`, or palette indices `0`-`255` on terminals with 256-color support

If the simulation falls into a repeating cycle, it pauses for a second and then restarts with a fresh random grid.

Exit the Game of Life visualization by pressing `Ctrl-C`, `q`, `Q`, or `Esc`.

## Tests
Run the automated test suite with:

`$ python3 -m unittest discover -s tests -p 'test*.py'`

## TODO
1. Optimize performance
2. Handle crashes after a while
3. Use a gif instead of a PNG for the example demonstration
4. Estimate memory usage tracking repeats
