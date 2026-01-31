"""Track delegated processes with rich progress meters.

Based on: https://www.deanmontgomery.com/2022/03/24/rich-progress-and-multiprocessing

"""

from __future__ import annotations

import math
import multiprocessing
from collections.abc import Callable
from concurrent.futures import ProcessPoolExecutor
from multiprocessing.managers import DictProxy
from time import sleep
from typing import Any, TypeVar

from rich.progress import BarColumn, Progress, ProgressColumn, TaskID, TimeElapsedColumn, TimeRemainingColumn

_ItemT = TypeVar('_ItemT', bound=Any)
"""Iterated item in the data."""


_DelegatedTask = Callable[
    [
        TaskID,
        DictProxy,  # type: ignore[type-arg]
        list[_ItemT],
    ],
    Any,
]


def _chunked(data: list[_ItemT], count: int) -> list[list[_ItemT]]:
    """Return the list of data split into count chunks of approximately equal size."""
    if not data or count <= 0:
        return [data] if data else []
    chunk_size = math.ceil(len(data) / count)
    return [data[i : i + chunk_size] for i in range(0, len(data), chunk_size)]


def pretty_process(
    delegated_task: _DelegatedTask,  # type: ignore[type-arg]
    *,
    data: list[_ItemT],
    num_workers: int = 3,
    num_cpus: int = 4,
) -> Any:
    """Run a task in parallel to process all provided data.

    Uses `rich` to display pretty progress bars

    Args:
        delegated_task: must call `shared_progress[task_id] += 1` on each item in data
        data: the list of data to distribute
        num_workers: number of worker processes
        num_cpus: number of CPUs

    Returns:
        List of results

    """
    # Docs: https://rich.readthedocs.io/en/latest/progress.html
    columns: list[str | ProgressColumn] = [
        '[progress.description]{task.description}',
        BarColumn(),
        '[progress.percentage]{task.percentage:>3.0f}%',
        TimeRemainingColumn(),
        TimeElapsedColumn(),
    ]
    with Progress(*columns, refresh_per_second=1) as progress:  # noqa: SIM117 (Py>3.9)
        # Share state between process and workers
        with multiprocessing.Manager() as manager:
            shared_progress = manager.dict()
            jobs = []
            totals = {}
            task_id_all = progress.add_task('[green]All jobs progress:')

            with ProcessPoolExecutor(max_workers=num_workers) as executor:
                for ix, chunk in enumerate(_chunked(data, count=num_cpus)):
                    task_id = progress.add_task(f'task {ix}')
                    shared_progress[task_id] = 0
                    totals[task_id] = len(chunk)
                    jobs.append(executor.submit(delegated_task, task_id, shared_progress, chunk))

                # Update progress bar from shared state
                remaining = len(jobs)
                while remaining:
                    n_done = 0
                    for task_id, latest in shared_progress.items():
                        n_done += latest
                        progress.update(task_id, completed=latest, total=totals[task_id])
                    progress.update(task_id_all, completed=n_done, total=len(data))
                    remaining = len(jobs) - sum(job.done() for job in jobs)
                    if remaining:
                        sleep(0.1)  # 100ms refresh rate to avoid busy-waiting

                # Collect results and catch any errors
                return [job.result() for job in jobs]


def ____private(task_id: int, shared_progress: DictProxy, data: list[_ItemT]) -> Any:  # type: ignore[type-arg]
    """Return True for testing a long running task.

    Note: this function can't be in the if-block below

    """
    for _val in data:
        sleep(1)
        shared_progress[task_id] += 1
    return True


if __name__ == '__main__':

    def _demo() -> None:
        """Run demo with: 'uv run shoal.pretty_process'."""
        # Resolve number of cores or specified maximum
        num_cpus = 4
        try:
            import psutil  # pyright: ignore[reportMissingModuleSource] # noqa: PLC0415

            num_cpus = psutil.cpu_count(logical=False) or num_cpus
        except Exception as exc:
            print(exc)  # noqa: T201

        result = pretty_process(____private, data=[*range(23)], num_workers=num_cpus)
        print(result)  # noqa: T201

    _demo()
