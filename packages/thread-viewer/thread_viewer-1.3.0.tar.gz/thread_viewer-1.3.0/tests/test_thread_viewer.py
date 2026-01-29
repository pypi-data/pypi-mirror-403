import unittest
from mock import patch
from mock import call
from mock import Mock
from thread_viewer import ThreadRowView
from thread_viewer import ThreadViewer
from colorama import Fore, Style

class TestThreadRowView(unittest.TestCase):

    def test_init_invalid_params(self):
        with self.assertRaises(ValueError):
            ThreadRowView(count=-1, width=2)
        with self.assertRaises(ValueError):
            ThreadRowView(count=5, width=0)

    def test_init_valid_params(self):
        count = 3
        width = 2
        trv = ThreadRowView(count=count, width=width)
        for i in range(count):
            self.assertIn(str(i).zfill(width), trv.x_axis)

    def test_render(self):
        count = 3
        width = 2
        trv = ThreadRowView(count=count, width=width, inactive_char='.')
        out = trv.render()
        cells = out.split(' ')
        self.assertEqual(len(cells), count)
        self.assertTrue(all(c == ('.' * width) for c in cells))

    def test_check(self):
        trv = ThreadRowView(count=2, width=2)
        with self.assertRaises(ValueError):
            trv._check(-1)
        with self.assertRaises(ValueError):
            trv._check(2)
        # should not raise
        trv._check(0)
        trv._check(1)

    @patch('thread_viewer.thread_viewer.secrets.choice')
    def test_activate_sets_cell_and_color_first_time(self, choice_mock):
        active_char = '#'
        width = 2
        trv = ThreadRowView(count=3, width=width, active_char=active_char)
        chosen = trv._COLORS[0]
        choice_mock.return_value = chosen

        trv.activate(1)

        self.assertEqual(trv.cell(1), f"{chosen}{active_char * width}{Style.RESET_ALL}")
        self.assertEqual(trv.cell_color(1), chosen)
        choice_mock.assert_called_once_with(trv._COLORS)

    @patch('thread_viewer.thread_viewer.secrets.choice')
    def test_activate_excludes_previous_color(self, choice_mock):
        active_char = '#'
        width = 2
        trv = ThreadRowView(count=3, width=width, active_char=active_char)
        prev = trv._COLORS[0]
        trv._colors[1] = prev

        chosen = trv._COLORS[1]
        choice_mock.return_value = chosen

        trv.activate(1)

        # verify choice() got options excluding prev
        (choices_passed,), _ = choice_mock.call_args
        self.assertNotIn(prev, choices_passed)

        # verify rendered cell matches chosen
        self.assertEqual(trv.cell(1), f"{chosen}{active_char * width}{Style.RESET_ALL}")
        self.assertEqual(trv.cell_color(1), chosen)

    @patch('thread_viewer.thread_viewer.secrets.choice')
    def test_deactivate_sets_cell_to_empty(self, choice_mock):
        width = 2
        trv = ThreadRowView(count=2, width=width, inactive_char='.')
        choice_mock.return_value = trv._COLORS[0]
        trv.activate(1)
        self.assertNotEqual(trv.cell(1), '.' * width)

        trv.deactivate(1)
        self.assertEqual(trv.cell(1), '.' * width)

    @patch('thread_viewer.thread_viewer.time.sleep')
    def test_deactivate_sleeps_when_seconds_provided(self, sleep_mock):
        trv = ThreadRowView(count=2, width=2)
        trv.deactivate(1, seconds=.3)
        sleep_mock.assert_called_once_with(.3)

    def test_reset_noop_on_empty_view(self):
        trv = ThreadRowView(count=0, width=2)
        trv.reset()  # should not raise
        self.assertEqual(trv.render(), '')  # join([]) == ''

    @patch('thread_viewer.thread_viewer.secrets.choice')
    def test_reset_clears_cells_and_color_history(self, choice_mock):
        count = 3
        width = 2
        trv = ThreadRowView(count=count, width=width, inactive_char='.')

        # activate a couple cells to dirty state
        choice_mock.return_value = trv._COLORS[0]
        trv.activate(0)
        choice_mock.return_value = trv._COLORS[1]
        trv.activate(2)

        # cells are not all empty anymore
        self.assertNotEqual(trv.cell(0), '.' * width)
        self.assertNotEqual(trv.cell(2), '.' * width)

        trv.reset()

        # every cell is empty again
        for i in range(count):
            self.assertEqual(trv.cell(i), '.' * width)

        # colors cleared
        for i in range(count):
            self.assertEqual(trv.cell_color(i), None)

class TestThreadViewer(unittest.TestCase):

    def test_init_invalid_params(self, *patches):
        with self.assertRaises(ValueError):
            ThreadViewer(thread_count=-1)
        with self.assertRaises(ValueError):
            ThreadViewer(thread_count=5, task_count=-1)
        with self.assertRaises(ValueError):
            ThreadViewer(thread_count=4, task_count=10, thread_prefix='')

    @patch('builtins.print')
    def test_get_thread_number(self, *patches):
        with ThreadViewer(thread_count=3, task_count=5, thread_prefix='worker_') as viewer:
            self.assertEqual(viewer._get_thread_number('worker_0'), 0)
            self.assertEqual(viewer._get_thread_number('worker_2'), 2)
            self.assertIsNone(viewer._get_thread_number('unknown_1'))

    @patch('builtins.print')
    def test_enter_resets_state(self, *patches):
        with ThreadViewer(thread_count=2, task_count=4) as viewer:
            self.assertEqual(viewer.get('Queued'), '4')
            self.assertEqual(viewer.get('Active'), '0')
            self.assertEqual(viewer.get('Closed'), '0')
            self.assertEqual(viewer.get('Thread'), viewer._thread_row_view.render())

    @patch('builtins.print')
    def test_run(self, *patches):
        with ThreadViewer(thread_count=2, task_count=4) as viewer:
            viewer.run('thread_1')
            self.assertEqual(viewer.get('Queued'), '3')
            self.assertEqual(viewer.get('Active'), '1')
            self.assertEqual(viewer.get('Closed'), '0')
            self.assertEqual(viewer.get('Thread'), viewer._thread_row_view.render())

    @patch('builtins.print')
    def test_run_with_unknown_thread(self, *patches):
        with ThreadViewer(thread_count=2, task_count=4) as viewer:
            viewer.run('unknown_thread')
            self.assertEqual(viewer.get('Queued'), '4')
            self.assertEqual(viewer.get('Active'), '0')
            self.assertEqual(viewer.get('Closed'), '0')
            self.assertEqual(viewer.get('Thread'), viewer._thread_row_view.render())

    @patch('builtins.print')
    def test_done(self, *patches):
        with ThreadViewer(thread_count=2, task_count=4) as viewer:
            viewer.run('thread_1')
            viewer.done('thread_1')
            self.assertEqual(viewer.get('Queued'), '3')
            self.assertEqual(viewer.get('Active'), '0')
            self.assertEqual(viewer.get('Closed'), '1')
            self.assertEqual(viewer.get('Thread'), viewer._thread_row_view.render())

    @patch('builtins.print')
    def test_done_with_unkown_thread(self, *patches):
        with ThreadViewer(thread_count=2, task_count=4) as viewer:
            viewer.run('thread_1')
            viewer.done('')
            self.assertEqual(viewer.get('Queued'), '2')
            self.assertEqual(viewer.get('Closed'), '1')
            self.assertEqual(viewer.get('Thread'), viewer._thread_row_view.render())
