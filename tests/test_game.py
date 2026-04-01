import sys
import tempfile
import unittest
from collections import deque
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
        recent_states = deque([game.grid_signature(first_state)], maxlen=game.MAX_TRACKED_STATES)

        self.assertTrue(game.is_repeated_state(recent_states, first_state))
        self.assertFalse(game.is_repeated_state(recent_states, second_state))

    def test_record_state_adds_signature_to_recent_states(self):
        state = [
            [0, 1, 0],
            [0, 1, 0],
            [0, 1, 0],
        ]
        recent_states = deque(maxlen=game.MAX_TRACKED_STATES)

        game.record_state(recent_states, state)

        self.assertEqual([game.grid_signature(state)], list(recent_states))

    def test_record_state_evicts_states_older_than_limit(self):
        recent_states = deque(maxlen=game.MAX_TRACKED_STATES)

        for index in range(game.MAX_TRACKED_STATES + 1):
            game.record_state(recent_states, [[index]])

        self.assertEqual(game.MAX_TRACKED_STATES, len(recent_states))
        self.assertEqual(game.grid_signature([[1]]), recent_states[0])
        self.assertEqual(game.grid_signature([[game.MAX_TRACKED_STATES]]), recent_states[-1])

    def test_restart_grids_pauses_before_creating_new_grids(self):
        new_grids = ([[1, 0]], [[0, 0]])

        with mock.patch.object(game.time, 'sleep') as sleep:
            with mock.patch.object(game, 'make_grids', return_value=new_grids) as make_grids:
                restarted_grids = game.restart_grids(1, 2)

        sleep.assert_called_once_with(game.RESTART_DELAY_SECONDS)
        make_grids.assert_called_once_with(1, 2)
        self.assertEqual(new_grids, restarted_grids)

    def test_get_memory_usage_kb_parses_ps_output(self):
        with mock.patch.object(game.subprocess, 'check_output', return_value=' 1234\n') as check_output:
            memory_usage_kb = game.get_memory_usage_kb()

        check_output.assert_called_once_with(
            ['ps', '-o', 'rss=', '-p', str(game.os.getpid())],
            universal_newlines=True,
        )
        self.assertEqual(1234, memory_usage_kb)

    def test_log_memory_usage_writes_sample_after_interval(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            log_path = temp_dir + '/game_debug.log'
            with mock.patch.object(game, 'get_memory_usage_kb', return_value=2048):
                with mock.patch.object(game, 'current_timestamp', return_value='2026-04-01T00:00:00'):
                    last_logged_at = game.log_memory_usage(
                        0.0,
                        3,
                        log_path=log_path,
                        current_time=game.MEMORY_LOG_INTERVAL_SECONDS,
                    )

            with open(log_path) as debug_log:
                log_contents = debug_log.read()

        self.assertEqual(game.MEMORY_LOG_INTERVAL_SECONDS, last_logged_at)
        self.assertIn('rss_kb=2048', log_contents)
        self.assertIn('tracked_states=3', log_contents)

    def test_log_memory_usage_skips_before_interval(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            log_path = temp_dir + '/game_debug.log'
            with mock.patch.object(game, 'get_memory_usage_kb') as get_memory_usage_kb:
                last_logged_at = game.log_memory_usage(
                    0.0,
                    3,
                    log_path=log_path,
                    current_time=game.MEMORY_LOG_INTERVAL_SECONDS - 0.1,
                )

        get_memory_usage_kb.assert_not_called()
        self.assertEqual(0.0, last_logged_at)

    def test_log_unhandled_exception_writes_traceback(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            log_path = temp_dir + '/game_debug.log'
            try:
                raise RuntimeError('boom')
            except RuntimeError:
                with mock.patch.object(game, 'current_timestamp', return_value='2026-04-01T00:00:00'):
                    game.log_unhandled_exception(log_path=log_path)

            with open(log_path) as debug_log:
                log_contents = debug_log.read()

        self.assertIn('unhandled_exception', log_contents)
        self.assertIn('RuntimeError: boom', log_contents)

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

    def test_parse_cli_arguments_uses_terminal_defaults(self):
        parsed_arguments = game.parse_cli_arguments(24, 40, argv=[])

        self.assertEqual(
            (24, 40, sys.maxsize, 0.04, game.DEFAULT_FOREGROUND_COLOR, game.DEFAULT_BACKGROUND_COLOR),
            parsed_arguments,
        )

    def test_parse_cli_arguments_accepts_named_options_without_steps(self):
        parsed_arguments = game.parse_cli_arguments(
            24,
            40,
            argv=['24', '40', '--delay', '0.1', '--fg', 'red', '--bg', 'black'],
        )

        self.assertEqual(
            (24, 40, sys.maxsize, 0.1, 'red', 'black'),
            parsed_arguments,
        )

    def test_parse_cli_arguments_allows_named_options_to_override_positionals(self):
        parsed_arguments = game.parse_cli_arguments(
            24,
            40,
            argv=['10', '20', '30', '0.1', 'red', 'black', '--steps', '50', '--delay', '0.2'],
        )

        self.assertEqual(
            (10, 20, 50, 0.2, 'red', 'black'),
            parsed_arguments,
        )

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

    def test_init_game_accepts_named_delay_and_color_arguments_without_steps(self):
        with mock.patch.object(
            sys,
            'argv',
            ['game.py', '10', '20', '--delay', '0.1', '--fg', '196', '--bg', '234'],
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
        self.assertEqual(sys.maxsize, steps)
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
