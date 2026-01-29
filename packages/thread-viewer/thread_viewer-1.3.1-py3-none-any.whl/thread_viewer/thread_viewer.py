import time
import secrets
from colorama import Fore, Style
from list2term import Lines


class ThreadRowView:
    """ Renders a single row representing thread activity.
        Each cell corresponds to a thread. When activated, the cell is displayed
        using the active character and a randomly chosen foreground color that
        differs from the previous activation to make activity visible even during
        rapid reuse of threads.
    """

    _COLORS = [
        Fore.RED,
        Fore.GREEN,
        Fore.YELLOW,
        Fore.BLUE,
        Fore.MAGENTA,
        Fore.CYAN,
    ]

    def __init__(self, count=0, width=1, active_char='█', inactive_char='░'):
        """ Initialize the thread row view.

        :param count: Number of thread cells to render.
        :param width: Width of each cell in characters.
        :param active_char: Character used to render an active cell.
        :param inactive_char: Character used to render an inactive cell.
        """
        if count < 0:
            raise ValueError('count must be >= 0')
        if width < 1:
            raise ValueError('width must be >= 1')

        self._active = active_char * width
        self._empty = inactive_char * width
        self._cells = [self._empty] * count
        self._x_axis = Style.BRIGHT + \
            ' '.join(str(i).zfill(width) for i in range(count)) + Style.RESET_ALL

        # Track the previously used color for each cell
        self._colors = [None] * count

    def activate(self, n):
        """ Mark cell `n` as active.
            Each activation selects a new foreground color different from the
            previously used color for that cell.
        """
        self._check(n)

        prev = self._colors[n]
        choices = self._COLORS if prev is None else [c for c in self._COLORS if c != prev]
        color = secrets.choice(choices)

        self._colors[n] = color
        # Render active cell with color and reset styles afterward
        self._cells[n] = f'{color}{self._active}{Style.RESET_ALL}'

    def deactivate(self, n, seconds=0):
        """ Mark cell `n` as inactive.
            Optionally sleeps for a short duration to make the inactive state
            visible for debugging or demos.
        """
        self._check(n)
        self._cells[n] = self._empty
        if seconds:
            time.sleep(seconds)

    def reset(self):
        """ Reset all cells to the inactive state and clear color history.
        """
        self._cells[:] = [self._empty] * len(self._cells)
        self._colors[:] = [None] * len(self._colors)

    def render(self):
        """ Return the rendered thread row as a single string.
        """
        return ' '.join(self._cells)

    def _check(self, n):
        """ Validate that cell index `n` is within bounds.
        """
        if n < 0 or n >= len(self._cells):
            raise ValueError(f'cell index out of range: {n}')

    def cell(self, n):
        """ Return the rendered string for cell `n`.
        """
        self._check(n)
        return self._cells[n]

    def cell_color(self, n):
        """ Return the color string for cell `n`, or None if inactive.
        """
        self._check(n)
        return self._colors[n]

    @property
    def x_axis(self):
        """ Return the precomputed x-axis label string for this row.
        """
        return self._x_axis


class ThreadViewer(Lines):
    """ Terminal-based viewer for thread pool activity.
        Displays queued, active, and completed task counts along with a visual
        representation of thread activity using a ThreadRowView.
    """

    def __init__(self, thread_count=0, task_count=0, thread_prefix='thread_'):
        """ Initialize the thread viewer.

        :param thread_count: Number of worker threads.
        :param task_count: Total number of tasks to process.
        :param thread_prefix: Prefix used to parse thread names.
        """
        if thread_count < 1:
            raise ValueError('thread_count must be >= 1')
        if task_count < 0:
            raise ValueError('task_count must be >= 0')
        if not thread_prefix:
            raise ValueError('thread_prefix must be non-empty')

        self._task_count = task_count
        self._thread_prefix = thread_prefix
        self._thread_width = len(str(thread_count - 1))

        self._labels = ('Thread', 'Queued', 'Active', 'Closed')
        self._idx = {name: i for i, name in enumerate(self._labels)}

        self._thread_row_view = ThreadRowView(
            count=thread_count,
            width=self._thread_width,
        )
        self._thread_row = self._idx['Thread']

        super().__init__(
            size=len(self._labels),
            show_x_axis=True,
            y_axis_labels=self._labels,
            x_axis=self._thread_row_view.x_axis,
            use_color=False,
            max_chars=5000,
        )

    def __enter__(self):
        """ Enter the Lines context and reset the viewer state.
        """
        super().__enter__()
        self.reset()
        return self

    def reset(self):
        """ Reset counters and clear thread activity display.
        """
        with self._lock:
            self._thread_row_view.reset()
            self._set('Queued', value=self._task_count)
            self._set('Active', value=0)
            self._set('Closed', value=0)
            self[self._thread_row] = self._thread_row_view.render()

    def run(self, thread_name):
        """ Mark a thread as started
        """
        n = self._get_thread_number(thread_name)
        if n is None:
            return
        with self._lock:
            self._decrement('Queued')
            self._increment('Active')
            self._thread_row_view.activate(n)
            self[self._thread_row] = self._thread_row_view.render()

    def done(self, thread_name):
        """ Mark a thread as completed
        """
        n = self._get_thread_number(thread_name)
        with self._lock:
            if n is not None:
                self._decrement('Active')
                self._increment('Closed')
                self._thread_row_view.deactivate(n, seconds=0)
                self[self._thread_row] = self._thread_row_view.render()
            else:
                # done event with no thread name occurs from a skip-dependency event
                # a task is skipped due to a dependency failure
                self._decrement('Queued')
                self._increment('Closed')

    def _decrement(self, name):
        """ Decrement the numeric value of a counter row.
        """
        i = self._idx[name]
        self[i] = str(int(self[i]) - 1)

    def _increment(self, name):
        """ Increment the numeric value of a counter row.
        """
        i = self._idx[name]
        self[i] = str(int(self[i]) + 1)

    def _set(self, name, value=0):
        """ Set a counter row to a specific value.
        """
        i = self._idx[name]
        self[i] = str(value)

    def _get_thread_number(self, thread_name):
        """ Extract the thread index from a thread name.
        """
        if not thread_name.startswith(self._thread_prefix):
            return
        return int(thread_name[len(self._thread_prefix):])

    def get(self, label):
        """ Return the string value of a row by label.
        """
        return self[self._idx[label]]
