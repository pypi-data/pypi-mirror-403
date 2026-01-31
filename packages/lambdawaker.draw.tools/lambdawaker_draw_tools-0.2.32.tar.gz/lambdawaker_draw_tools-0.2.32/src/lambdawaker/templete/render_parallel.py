#!/usr/bin/env python3
import argparse
import os
import sys
from pathlib import Path

import requests

from lambdawaker.executor.engine import SubprocessExecutor
from lambdawaker.executor.models import TaskConfig
from lambdawaker.executor.reporter import RichReporter

DATASET_LEN_URL = "http://localhost:8001/ds/lambdaWalker/ds.photo_id/body/len"
WORKER_SCRIPT = Path(__file__).parent / "render_in_series.py"


def fetch_dataset_size(url: str) -> int:
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        # Handle quoted strings from some API responses
        return int(resp.text.strip().strip('"').strip("'"))
    except Exception as e:
        print(f"Error fetching dataset size from {url}: {e}")
        # Default to a safe value or re-raise
        raise RuntimeError(f"Failed to fetch dataset size: {e}")


def run_dispatcher(args):
    total = fetch_dataset_size(args.dataset_url)

    cpu_count = os.cpu_count() or 1
    worker_count = max(4, round(cpu_count * (args.worker_load_percent / 100.0)))

    config = TaskConfig(
        total_items=total,
        num_workers=worker_count,
        max_retries=args.max_retries,
        refresh_hz=args.refresh_hz,
        grid_cols=args.grid_cols
    )

    def get_command(state):
        start = state.extra_data['start_index']
        end = state.extra_data['end_index']
        cmd = [
            sys.executable, str(WORKER_SCRIPT),
            "--start", str(start),
            "--end", str(end),
            "--base-url", args.base_url,
            "--outdir", args.outdir,
        ]
        if args.headless:
            cmd.append("--headless")
        else:
            cmd.append("--no-headless")
        return cmd

    executor = SubprocessExecutor(config, get_command)
    reporter = RichReporter(title=f"Parallel Rendering ({worker_count} Workers)")

    executor.run(reporter)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--worker-load-percent", type=int, default=85)
    p.add_argument("--grid-cols", type=int, default=8)
    p.add_argument("--refresh-hz", type=float, default=24.0)
    p.add_argument("--max-retries", type=int, default=3)
    p.add_argument("--dataset-url", default=DATASET_LEN_URL)
    p.add_argument("--base-url", default="http://127.0.0.1:8001")
    p.add_argument("--outdir", default="./output/img/")
    p.add_argument("--headless", action=argparse.BooleanOptionalAction, default=True)

    run_dispatcher(p.parse_args())
