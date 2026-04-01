import sys
import unittest
from unittest import mock

import game


class DummyScreen(object):
    def getmaxyx(self):
        return (24, 80)

    def timeout(self, value):
        self.timeout_value = value


class GameTests(unittest.TestCase):
    def test_rand_init_grid_returns_requested_shape(self):
        grid = game.rand_init_grid(3, 4)

        self.assertEqual(3, len(grid))
        self.assertTrue(all(len(row) == 4 for row in grid))
        self.assertTrue(all(cell in (0, 1) for row in grid for cell in row))

    def test_rand_init_grid_with_border_creates_dead_edges(self):
        grid = game.rand_init_grid(4, 5, with_border=True)

        self.assertEqual([0, 0, 0, 0, 0], grid[0])
        self.assertEqual([0, 0, 0, 0, 0], grid[-1])
        self.assertTrue(all(row[0] == 0 and row[-1] == 0 for row in grid))

    def test_imported_module_supports_python3_helpers(self):
        grid = game.rand_init_grid(2, 3)

        self.assertEqual(2, len(grid))
        self.assertEqual(3, len(grid[0]))

    def test_print_grid_returns_expected_bytes(self):
        rendered = game.print_grid([[1, 0], [0, 1]])

        self.assertEqual(b'\xe2\x96\x84  \n  \xe2\x96\x84', rendered)

    def test_should_exit_recognizes_supported_exit_keys(self):
        self.assertTrue(game.should_exit(ord('q')))
        self.assertTrue(game.should_exit(ord('Q')))
        self.assertTrue(game.should_exit(27))
        self.assertFalse(game.should_exit(-1))

    def test_configure_input_reduces_escape_delay(self):
        screen = DummyScreen()

        with mock.patch.object(game.curses, 'set_escdelay') as set_escdelay:
            game.configure_input(screen, 0.04)

        set_escdelay.assert_called_once_with(game.ESC_DELAY_MS)
        self.assertEqual(40, screen.timeout_value)

    def test_live_neighbor_count_counts_wrapped_neighbors(self):
        grid = [
            [1, 0, 0],
            [0, 1, 0],
            [0, 0, 0],
        ]

        self.assertEqual(1, game.live_neighbor_count(1, 1, grid))
        self.assertEqual(1, game.live_neighbor_count(0, 0, grid))

    def test_cell_transition_applies_underpopulation(self):
        grid = [
            [0, 0, 0],
            [0, 1, 0],
            [0, 0, 0],
        ]

        self.assertEqual(0, game.cell_transition(1, 1, grid))

    def test_cell_transition_applies_survival(self):
        grid = [
            [1, 1, 0],
            [0, 1, 0],
            [0, 0, 0],
        ]

        self.assertEqual(1, game.cell_transition(1, 1, grid))

    def test_cell_transition_applies_overpopulation(self):
        grid = [
            [1, 1, 1],
            [1, 1, 0],
            [0, 0, 0],
        ]

        self.assertEqual(0, game.cell_transition(1, 1, grid))

    def test_cell_transition_applies_reproduction(self):
        grid = [
            [1, 1, 0],
            [1, 0, 0],
            [0, 0, 0],
        ]

        self.assertEqual(1, game.cell_transition(1, 1, grid))

    def test_init_game_honors_partial_cli_arguments(self):
        with mock.patch.object(sys, 'argv', ['game.py', '10', '20']):
            grid_1, grid_2, steps, refresh_time = game.init_game(DummyScreen())

        self.assertEqual(10, len(grid_1))
        self.assertEqual(20, len(grid_1[0]))
        self.assertEqual(10, len(grid_2))
        self.assertEqual(20, len(grid_2[0]))
        self.assertEqual(sys.maxsize, steps)
        self.assertEqual(0.04, refresh_time)

    def test_state_transition_preserves_dead_border(self):
        current = [
            [0, 0, 0, 0, 0],
            [0, 1, 1, 1, 0],
            [0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0],
        ]
        future = [[9] * 5 for _ in range(5)]

        game.state_transition(current, future, with_border=True)

        self.assertEqual([0, 0, 0, 0, 0], future[0])
        self.assertEqual([0, 0, 0, 0, 0], future[-1])
        self.assertEqual([0, 0, 1, 0, 0], future[1])
        self.assertEqual([0, 0, 1, 0, 0], future[2])
        self.assertTrue(all(row[0] == 0 and row[-1] == 0 for row in future))

    def test_state_transition_preserves_still_life_block(self):
        current = [
            [0, 0, 0, 0],
            [0, 1, 1, 0],
            [0, 1, 1, 0],
            [0, 0, 0, 0],
        ]
        future = [[0] * 4 for _ in range(4)]

        game.state_transition(current, future)

        self.assertEqual(current, future)


if __name__ == '__main__':
    unittest.main()
