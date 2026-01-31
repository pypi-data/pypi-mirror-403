import argparse
import random
import sys
import time


def mock_worker():
    parser = argparse.ArgumentParser()
    parser.add_argument("--total", type=int, default=100)
    args = parser.parse_args()

    total = args.total

    print(f"STATUS: RUNNING")
    print(f"MESSAGE: Starting mock work...")

    for i in range(1, total + 1):
        time.sleep(random.uniform(0.01, 0.1))
        print(f"PROGRESS: {i}")

        if i == total // 2 and random.random() < 0.1:
            print(f"STATUS: FAILED")
            print(f"MESSAGE: Random failure at {i}")
            sys.exit(1)

        if i % 10 == 0:
            print(f"MESSAGE: Processed {i} items...")

    print(f"STATUS: SUCCESS")
    print(f"MESSAGE: Completed all items")


if __name__ == "__main__":
    mock_worker()
