import sys
from pathlib import Path

from lambdawaker.executor.engine import SubprocessExecutor
from lambdawaker.executor.models import TaskConfig
from lambdawaker.executor.reporter import RichReporter


def run_demo():
    config = TaskConfig(
        total_items=1000,
        num_workers=8,
        max_retries=3,
        grid_cols=4
    )

    mock_task_script = Path(__file__).parent / "mock_task.py"

    def get_command(state):
        return [
            sys.executable,
            str(mock_task_script),
            "--total", str(state.total)
        ]

    executor = SubprocessExecutor(
        config,
        get_command
    )

    reporter = RichReporter(title="Demo Parallel Mock Task")
    executor.run(reporter_func=reporter)


if __name__ == "__main__":
    run_demo()
