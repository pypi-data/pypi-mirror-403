import functools
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, ParamSpec, Self, TypeVar, overload

T = TypeVar("T")
P = ParamSpec("P")

@dataclass
class Timing:
    """
    A high-resolution timer that can be used as a context manager, decorator
    or manually.

    Attributes
    ----------
    nanoseconds : float
        The elapsed time in nanoseconds.
    microseconds : float
        The elapsed time in microseconds.
    milliseconds : float
        The elapsed time in milliseconds.
    seconds : float
        The elapsed time in seconds.
    minutes : float
        The elapsed time in minutes.
    hours : float
        The elapsed time in hours.
    elapsed : str
        The elapsed time as a formatted string in seconds.
    is_running : bool
        Whether the timer is currently running.

    Example
    -------
    As a context manager::
    
        with Timing() as timer:
            # code to time
        print(timer.elapsed) # prints 'Elapsed time: 0.123456s'
    
    As a decorator::

        @Timing # Works both with and without parenthesis
        def my_function():
            # code to time
        my_function() # prints 'Function 'my_function' took 0.123456s'

    Direct call::

        def my_function(x):
            # code to time
        timer = Timing(my_function)
        result = timer(10) # prints 'Function 'my_function' took 0.123456s'
        # timer attributes are still available: timer.seconds
    
    Manually::

        timer = Timing()
        timer.start()
        # code to time
        timer.stop()
        print(timer.seconds) # prints elapsed time in seconds
    
    Note
    ----
    - When used as a decorator, Timing prints the elapsed time to standard output.
    - When used as a context manager or manually, the elapsed time can be accessed
      via the properties.
    - The timer uses time.perf_counter_ns() for high-resolution timing.
    - The timer raises `RuntimeError` if the elapsed time is accessed before stopping.
    """
    __slots__ = ("_start_ns", "_end_ns", "_fn")

    @overload
    def __init__(self, fn: Callable[..., Any], /) -> None: ...
    @overload
    def __init__(self, /) -> None: ...

    def __init__(self, fn: Callable[..., Any] | None = None, /) -> None:
        self._fn: Callable[..., Any] | None = fn
        self._start_ns: int | None = None
        self._end_ns: int | None = None
    
    # ------------------------------------------------------------------------
    # Context manager API
    # ------------------------------------------------------------------------
    def __enter__(self) -> Self:
        self.start()
        return self

    def __exit__(self, *args: Any) -> None:
        self.stop()
    
    # ------------------------------------------------------------------------
    # Decorator API
    # ------------------------------------------------------------------------
    def _wrap[**P, T](self, target: Callable[P, T]) -> Callable[P, T]:
        @functools.wraps(target)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            with self:
                result = target(*args, **kwargs)

            # This runs after __exit__, so self.seconds is now available
            print(f"Function {target.__name__!r} took {self.seconds:06.6f}s")
            return result
        return wrapper

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        # Case 1: @Timing (no parenthesis)
        # In this case, __init__ is called with the function.
        # Python's decorator syntax @Timing works by calling
        # Timing(fn). So __init__(fn) is called.
        
        # If used as @Timing, __init__ receives the function.
        # If used as @Timing(), __init__ receives nothing, then
        # __call__ receives the function.

        if self._fn is not None:
            # This handles both:
            # 1. @Timing (where __init__ got the function)
            # 2. Timing(fn)(*args) (direct call)
            # If we already have a function and we are called with
            # arguments, it means we are executing the wrapped function.
            return self._wrap(self._fn)(*args, **kwargs)

        # Case 2: @Timing() or Timing() as CM
        # Here __init__ is called without fn.
        # Now __call__ is called.
        if len(args) == 1 and callable(args[0]) and not kwargs:
            # This is @Timing()
            return self._wrap(args[0])

        raise TypeError("Timing doesn't support arguments.")
    
    # ------------------------------------------------------------------------
    # Timing control
    # ------------------------------------------------------------------------
    def start(self) -> None:
        """Start the timer."""
        self._start_ns = time.perf_counter_ns()
        self._end_ns = None
    
    def stop(self) -> None:
        """Stop the timer."""
        self._end_ns = time.perf_counter_ns()

    # ------------------------------------------------------------------------
    # Core timing values
    # ------------------------------------------------------------------------
    @property
    def nanoseconds(self) -> float:
        """The elapsed time in nanoseconds."""
        if self._start_ns is None or self._end_ns is None:
            raise RuntimeError("Timer not finished")
        return self._end_ns - self._start_ns
    
    @property
    def microseconds(self) -> float:
        """The elapsed time in microseconds."""
        return self.nanoseconds / 1_000
    
    @property
    def milliseconds(self) -> float:
        """The elapsed time in milliseconds."""
        return self.nanoseconds / 1_000_000
    
    @property
    def seconds(self) -> float:
        """The elapsed time in seconds."""
        return self.nanoseconds / 1_000_000_000
    
    @property
    def minutes(self) -> float:
        """The elapsed time in minutes."""
        return self.seconds / 60
    
    @property
    def hours(self) -> float:
        """The elapsed time in hours."""
        return self.minutes / 60
    
    # ------------------------------------------------------------------------
    # Convenience properties
    # ------------------------------------------------------------------------
    @property
    def elapsed(self) -> str:
        """The elapsed time as a formatted string in seconds."""
        return f"Elapsed time: {self.seconds:06.6f}s"
    
    @property
    def is_running(self) -> bool:
        """Whether the timer is currently running."""
        return self._start_ns is not None and self._end_ns is None