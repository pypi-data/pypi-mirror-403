"""Shared parallel execution utilities using joblib."""

from itertools import islice
from typing import Any, Callable, Iterable, Iterator

import SimpleITK as sitk
from joblib import Parallel, delayed
from loguru import logger
from threadpoolctl import threadpool_limits

from mircat_v2.configs import logger_setup


def batched(iterable: Iterable, n: int) -> Iterator[tuple]:
    """Batch data from the iterable into tuples of length n.

    The last batch may be shorter than n. This is a backport of
    itertools.batched from Python 3.12.

    Args:
        iterable: The iterable to batch
        n: The batch size

    Yields:
        Tuples of length n (or less for the final batch)
    """
    if n < 1:
        raise ValueError("n must be at least one")
    iterator = iter(iterable)
    while batch := tuple(islice(iterator, n)):
        yield batch


def _worker_wrapper(
    func: Callable,
    item: Any,
    threads_per_job: int,
    verbose: bool,
    quiet: bool,
) -> Any:
    """Wrapper that sets up thread limits and logger before calling the worker function.

    Args:
        func: The worker function to call
        item: The item to pass to the worker function
        threads_per_job: Thread limit per job (for threadpoolctl + SimpleITK)
        verbose: Verbose logging flag
        quiet: Quiet logging flag

    Returns:
        The result of calling func(item)
    """
    logger_setup(verbose, quiet)
    sitk.ProcessObject.SetGlobalDefaultNumberOfThreads(threads_per_job)
    with threadpool_limits(threads_per_job):
        return func(item)


def run_parallel(
    func: Callable,
    items: Iterable,
    n_jobs: int = 1,
    threads_per_job: int = 4,
    verbose: bool = False,
    quiet: bool = False,
    on_complete: Callable[[int, int, Any], None] | None = None,
) -> tuple[list, bool]:
    """Run a function in parallel using joblib with KeyboardInterrupt handling.

    Args:
        func: The worker function to call on each item
        items: Iterable of items to process
        n_jobs: Number of parallel jobs
        threads_per_job: Thread limit per job (for threadpoolctl + SimpleITK)
        verbose: Verbose logging flag
        quiet: Quiet logging flag
        on_complete: Optional callback called after each item completes.
                     Signature: on_complete(current_index, total_items, result)
                     Called with 1-based index as items finish.

    Returns:
        Tuple of (results_list, was_interrupted)
        - results_list: List of results from completed function calls
        - was_interrupted: True if KeyboardInterrupt was caught
    """
    items_list = list(items)
    total = len(items_list)
    results = []

    try:
        parallel = Parallel(n_jobs=n_jobs, backend="loky", return_as="generator_unordered")
        generator = parallel(
            delayed(_worker_wrapper)(func, item, threads_per_job, verbose, quiet)
            for item in items_list
        )

        for i, result in enumerate(generator, start=1):
            results.append(result)
            if on_complete:
                on_complete(i, total, result)

        return results, False
    except KeyboardInterrupt:
        logger.warning("KeyboardInterrupt received - cleaning up...")
        return results, True
