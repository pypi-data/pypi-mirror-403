import os
import subprocess
import threading
import time
from abc import ABC, abstractmethod
from typing import List, Callable, Optional

from .models import WorkerState, TaskStatus, TaskConfig


class ProtocolHandler:
    """Handles the communication protocol between worker processes and the executor."""

    @staticmethod
    def parse_line(line: str, state: WorkerState) -> bool:
        """
        Parses a line from the worker output.
        Expected formats:
        PROGRESS: <int>
        STATUS: <str>
        MESSAGE: <str>
        """
        line = line.strip()
        if line.startswith("PROGRESS:"):
            try:
                val = int(float(line.split(":", 1)[1]))
                state.completed = val
                return True
            except (ValueError, IndexError):
                pass
        elif line.startswith("STATUS:"):
            try:
                status_str = line.split(":", 1)[1].strip().upper()
                if status_str in TaskStatus.__members__:
                    state.status = TaskStatus[status_str]
                return True
            except IndexError:
                pass
        elif line.startswith("MESSAGE:"):
            try:
                state.message = line.split(":", 1)[1].strip()
                return True
            except IndexError:
                pass
        return False


class BaseExecutor(ABC):
    def __init__(self, config: TaskConfig):
        self.config = config
        self.states: List[WorkerState] = []
        self._global_completed = 0
        self._lock = threading.Lock()
        self._stop_event = threading.Event()

    @property
    def global_completed(self) -> int:
        with self._lock:
            # We recalculate to be safe, or we could update it incrementally
            return sum(s.completed for s in self.states)

    @abstractmethod
    def run(self):
        pass


class SubprocessExecutor(BaseExecutor):
    def __init__(self, config: TaskConfig, get_command_func: Callable[[WorkerState], List[str]]):
        super().__init__(config)
        self.get_command_func = get_command_func
        self._setup_states()

    def _setup_states(self):
        base, rem = divmod(self.config.total_items, self.config.num_workers)
        start = 0
        for i in range(self.config.num_workers):
            size = base + (1 if i < rem else 0)
            state = WorkerState(
                worker_id=i,
                name=f"Worker-{i + 1}",
                total=size,
                extra_data={'start_index': start, 'end_index': start + size}
            )
            self.states.append(state)
            start += size

    def _run_worker(self, state: WorkerState):
        while state.attempts < self.config.max_retries and not self._stop_event.is_set():
            state.attempts += 1
            state.status = TaskStatus.RUNNING

            cmd = self.get_command_func(state)

            try:
                proc = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    env={**os.environ, "PYTHONUNBUFFERED": "1"}
                )

                for line in iter(proc.stdout.readline, ""):
                    if self._stop_event.is_set():
                        proc.terminate()
                        break
                    ProtocolHandler.parse_line(line, state)

                proc.wait()
                if proc.returncode == 0:
                    state.status = TaskStatus.SUCCESS
                    state.completed = state.total  # Ensure it's marked as done
                    return
                else:
                    state.status = TaskStatus.FAILED
                    state.message = f"Exit code: {proc.returncode}"
            except Exception as e:
                state.status = TaskStatus.CRASHED
                state.message = str(e)

            if state.attempts < self.config.max_retries and not self._stop_event.is_set():
                state.status = TaskStatus.RETRYING
                time.sleep(1)

        if state.status != TaskStatus.SUCCESS:
            state.status = TaskStatus.FINISHED if state.completed >= state.total else TaskStatus.FAILED

    def run(self, reporter_func: Optional[Callable] = None):
        threads = []
        for state in self.states:
            t = threading.Thread(target=self._run_worker, args=(state,), daemon=True)
            threads.append(t)
            t.start()

        if reporter_func:
            reporter_func(self, threads)
        else:
            for t in threads:
                t.join()
