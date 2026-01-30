"""Bounded thread pool executor with queue size limits."""

from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from threading import BoundedSemaphore


class BoundedExecutor:
    """BoundedExecutor behaves as a ThreadPoolExecutor which will block on calls to submit().

    Blocks once the limit given as "bound" work items are queued for execution.

    :param bound: Integer - the maximum number of items in the work queue
    :param max_workers: Integer - the size of the thread pool
    """

    def __init__(self, bound: int, max_workers: int) -> None:
        """Initialize the bounded executor.

        Args:
            bound: Maximum number of items in the work queue.
            max_workers: Size of the thread pool.
        """
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.semaphore = BoundedSemaphore(bound + max_workers)

    """See concurrent.futures.Executor#submit"""

    def submit(
        self, fn: Callable[..., object], *args: object, **kwargs: object
    ) -> object:
        """Submit a callable to be executed with bounded concurrency."""
        self.semaphore.acquire()
        try:
            future = self.executor.submit(fn, *args, **kwargs)
        except Exception:
            self.semaphore.release()
            raise
        else:
            future.add_done_callback(lambda _: self.semaphore.release())
            return future

    """See concurrent.futures.Executor#shutdown"""

    def shutdown(self, wait: bool = True) -> None:
        """Shutdown the executor, optionally waiting for pending tasks to complete."""
        self.executor.shutdown(wait)
