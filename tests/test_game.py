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

    def test_make_grids_returns_current_and_empty_future_grid(self):
        current_grid, future_grid = game.make_grids(3, 4)

        self.assertEqual(3, len(current_grid))
        self.assertTrue(all(len(row) == 4 for row in current_grid))
        self.assertEqual([[0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]], future_grid)

    def test_grid_signature_returns_hashable_state(self):
        signature = game.grid_signature([[1, 0], [0, 1]])

        self.assertEqual(((1, 0), (0, 1)), signature)

    def test_is_repeated_state_reports_previous_states(self):
        first_state = [
            [0, 1, 0],
            [0, 1, 0],
            [0, 1, 0],
        ]
        second_state = [
            [0, 0, 0],
            [1, 1, 1],
            [0, 0, 0],
        ]
        seen_states = {game.grid_signature(first_state)}

        self.assertTrue(game.is_repeated_state(seen_states, first_state))
        self.assertFalse(game.is_repeated_state(seen_states, second_state))

    def test_record_state_adds_signature_to_seen_states(self):
        state = [
            [0, 1, 0],
            [0, 1, 0],
            [0, 1, 0],
        ]
        seen_states = set()

        game.record_state(seen_states, state)

        self.assertEqual({game.grid_signature(state)}, seen_states)

    def test_restart_grids_pauses_before_creating_new_grids(self):
        new_grids = ([[1, 0]], [[0, 0]])

        with mock.patch.object(game.time, 'sleep') as sleep:
            with mock.patch.object(game, 'make_grids', return_value=new_grids) as make_grids:
                restarted_grids = game.restart_grids(1, 2)

        sleep.assert_called_once_with(game.RESTART_DELAY_SECONDS)
        make_grids.assert_called_once_with(1, 2)
        self.assertEqual(new_grids, restarted_grids)

    def test_parse_color_normalizes_case(self):
        self.assertEqual('green', game.parse_color('Green'))

    def test_parse_color_accepts_palette_index(self):
        self.assertEqual(196, game.parse_color('196'))

    def test_parse_color_rejects_unknown_color(self):
        with self.assertRaises(ValueError):
            game.parse_color('orange')

    def test_parse_color_rejects_out_of_range_palette_index(self):
        with self.assertRaises(ValueError):
            game.parse_color('256')

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

    def test_configure_colors_initializes_requested_pair(self):
        with mock.patch.object(game.curses, 'start_color') as start_color:
            with mock.patch.object(game.curses, 'init_pair') as init_pair:
                with mock.patch.object(game.curses, 'color_pair', return_value=123):
                    color_pair = game.configure_colors('red', 'black')

        start_color.assert_called_once_with()
        init_pair.assert_called_once_with(
            1,
            game.COLOR_NAME_TO_CURSES['red'],
            game.COLOR_NAME_TO_CURSES['black'],
        )
        self.assertEqual(123, color_pair)

    def test_configure_colors_accepts_palette_indices(self):
        with mock.patch.object(game.curses, 'COLORS', 256, create=True):
            with mock.patch.object(game.curses, 'start_color'):
                with mock.patch.object(game.curses, 'init_pair') as init_pair:
                    with mock.patch.object(game.curses, 'color_pair', return_value=456):
                        color_pair = game.configure_colors(196, 234)

        init_pair.assert_called_once_with(1, 196, 234)
        self.assertEqual(456, color_pair)

    def test_configure_colors_rejects_unsupported_palette_index(self):
        with mock.patch.object(game.curses, 'COLORS', 8, create=True):
            with mock.patch.object(game.curses, 'start_color'):
                with self.assertRaises(ValueError):
                    game.configure_colors(196, 'black')

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
            (
                grid_1,
                grid_2,
                steps,
                refresh_time,
                foreground_color,
                background_color,
            ) = game.init_game(DummyScreen())

        self.assertEqual(10, len(grid_1))
        self.assertEqual(20, len(grid_1[0]))
        self.assertEqual(10, len(grid_2))
        self.assertEqual(20, len(grid_2[0]))
        self.assertEqual(sys.maxsize, steps)
        self.assertEqual(0.04, refresh_time)
        self.assertEqual(game.DEFAULT_FOREGROUND_COLOR, foreground_color)
        self.assertEqual(game.DEFAULT_BACKGROUND_COLOR, background_color)

    def test_init_game_accepts_optional_color_arguments(self):
        with mock.patch.object(
            sys,
            'argv',
            ['game.py', '10', '20', '30', '0.1', 'red', 'black'],
        ):
            (
                grid_1,
                grid_2,
                steps,
                refresh_time,
                foreground_color,
                background_color,
            ) = game.init_game(DummyScreen())

        self.assertEqual(10, len(grid_1))
        self.assertEqual(20, len(grid_1[0]))
        self.assertEqual(10, len(grid_2))
        self.assertEqual(20, len(grid_2[0]))
        self.assertEqual(30, steps)
        self.assertEqual(0.1, refresh_time)
        self.assertEqual('red', foreground_color)
        self.assertEqual('black', background_color)

    def test_init_game_accepts_palette_index_arguments(self):
        with mock.patch.object(
            sys,
            'argv',
            ['game.py', '10', '20', '30', '0.1', '196', '234'],
        ):
            (
                grid_1,
                grid_2,
                steps,
                refresh_time,
                foreground_color,
                background_color,
            ) = game.init_game(DummyScreen())

        self.assertEqual(10, len(grid_1))
        self.assertEqual(20, len(grid_1[0]))
        self.assertEqual(10, len(grid_2))
        self.assertEqual(20, len(grid_2[0]))
        self.assertEqual(30, steps)
        self.assertEqual(0.1, refresh_time)
        self.assertEqual(196, foreground_color)
        self.assertEqual(234, background_color)

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
