from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Dict, Any

from rich.progress import Progress


class TaskStatus(Enum):
    PENDING = "Pending"
    RUNNING = "Running"
    SUCCESS = "Success"
    FAILED = "Failed"
    CRASHED = "Crashed"
    RETRYING = "Retrying"
    FINISHED = "Finished"


@dataclass
class WorkerState:
    worker_id: int
    name: str
    total: int
    completed: int = 0
    status: TaskStatus = TaskStatus.PENDING
    message: str = ""
    attempts: int = 0
    extra_data: Dict[str, Any] = field(default_factory=dict)

    # UI related
    progress_obj: Optional[Progress] = None
    task_id: Optional[int] = None


@dataclass
class TaskConfig:
    total_items: int
    num_workers: int
    max_retries: int = 3
    refresh_hz: float = 10.0
    grid_cols: int = 4
