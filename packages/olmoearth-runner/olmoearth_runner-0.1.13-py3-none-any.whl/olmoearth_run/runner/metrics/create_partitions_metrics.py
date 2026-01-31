from collections.abc import Callable
from functools import wraps
from timeit import default_timer
from typing import Any, ParamSpec, TypeVar

from prometheus_client import Histogram
from prometheus_client.context_managers import Timer

_timer = Histogram(
    'runner_create_partitions_timer',
    'Timers for various operations the create partitions step',
    labelnames=['method_name']
)

P = ParamSpec("P")
T = TypeVar("T")


class CreatePartitionsMetrics:

    @staticmethod
    def time_function(func: Callable[P, T]) -> Callable[P, T]:
        """Decorator to time a method and record the duration"""

        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            start = default_timer()
            try:
                return func(*args, **kwargs)
            finally:
                duration = default_timer() - start
                _timer.labels(method_name=func.__name__).observe(duration)
        return wrapper

    @staticmethod
    def time_block(name: str) -> Timer:
        """Method that returns a prometheus timer that can be used in a with statement."""
        return _timer.labels(method_name=name).time()
