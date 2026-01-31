import time
from typing import List

from rich.console import Group
from rich.live import Live
from rich.panel import Panel
from rich.progress import (
    Progress,
    BarColumn,
    TextColumn,
    SpinnerColumn,
    TimeRemainingColumn,
    TaskProgressColumn,
    TimeElapsedColumn,
    MofNCompleteColumn
)
from rich.table import Table
from rich.text import Text

from .engine import BaseExecutor
from .models import WorkerState, TaskStatus


class RichReporter:
    def __init__(self, title: str = "Parallel Task Execution"):
        self.title = title
        self.total_progress = Progress(
            TextColumn("[bold blue]{task.description}[/]"),
            SpinnerColumn(),
            TaskProgressColumn(),
            SpinnerColumn(),
            BarColumn(bar_width=None),
            SpinnerColumn(),
            TimeElapsedColumn(),
            SpinnerColumn(),
            MofNCompleteColumn(),
            SpinnerColumn(),
            TimeRemainingColumn()
        )
        self.total_task_id = None

    def get_worker_panel(self, state: WorkerState) -> Panel:
        label = state.name

        if state.progress_obj is None:
            state.progress_obj = Progress(
                BarColumn(),
                TextColumn("{task.completed}/{task.total}"),
                TimeRemainingColumn(),
                expand=True,
            )
            state.task_id = state.progress_obj.add_task(label, total=state.total)

        state.progress_obj.update(state.task_id, completed=state.completed)

        status_color = "yellow"
        if state.status in [TaskStatus.FAILED, TaskStatus.CRASHED]:
            status_color = "bold red"
        elif state.status == TaskStatus.SUCCESS:
            status_color = "bold green"
        elif state.status == TaskStatus.RUNNING:
            status_color = "cyan"

        status_display = state.status.value
        if state.message:
            status_display += f" ({state.message})"

        title = Text.assemble(
            (status_display, status_color),
            ("  •  ", "dim"),
            (label, "bold white")
        )

        start_idx = state.extra_data.get('start_index', '?')
        end_idx = state.extra_data.get('end_index', '?')
        subtitle = Text.assemble(
            ("range ", "dim"), (f"{start_idx}..{end_idx}", "dim"),
            ("  •  ", "dim"), (f"try {state.attempts}", "dim")
        )

        return Panel(state.progress_obj, title=title, subtitle=subtitle)

    def render_grid(self, executor: BaseExecutor) -> Group:
        self.total_progress.update(self.total_task_id, completed=executor.global_completed)

        panels = [self.get_worker_panel(st) for st in executor.states]
        grid = Table.grid(expand=True)
        cols = executor.config.grid_cols
        for _ in range(cols):
            grid.add_column(ratio=1)

        for i in range(0, len(panels), cols):
            row = panels[i:i + cols]
            while len(row) < cols:
                row.append("")
            grid.add_row(*row)

        return Group(self.total_progress, grid)

    def __call__(self, executor: BaseExecutor, threads: List):
        self.total_task_id = self.total_progress.add_task(self.title, total=executor.config.total_items)

        with Live(refresh_per_second=executor.config.refresh_hz, transient=False) as live:
            while any(t.is_alive() for t in threads):
                live.update(self.render_grid(executor))
                time.sleep(1 / executor.config.refresh_hz)
            live.update(self.render_grid(executor))
