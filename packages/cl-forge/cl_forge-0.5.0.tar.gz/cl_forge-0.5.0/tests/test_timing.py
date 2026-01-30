import time

import pytest

from cl_forge.core.timing import Timing


def test_manual_timing():
    timer = Timing()
    assert not timer.is_running
    with pytest.raises(RuntimeError, match="Timer not finished"):
        _ = timer.seconds

    timer.start()
    assert timer.is_running
    time.sleep(0.01)
    timer.stop()
    assert not timer.is_running
    
    assert timer.nanoseconds > 0
    assert timer.microseconds == timer.nanoseconds / 1_000
    assert timer.milliseconds == timer.nanoseconds / 1_000_000
    assert timer.seconds == timer.nanoseconds / 1_000_000_000
    assert timer.minutes == timer.seconds / 60
    assert timer.hours == timer.minutes / 60
    assert "Elapsed time:" in timer.elapsed

def test_context_manager_timing():
    with Timing() as timer:
        assert timer.is_running
        time.sleep(0.01)
    
    assert not timer.is_running
    assert timer.seconds >= 0.01

def test_decorator_timing(capsys):
    @Timing
    def slow_func(x):
        time.sleep(0.01)
        return x * 2

    result = slow_func(5)
    assert result == 10
    
    captured = capsys.readouterr()
    assert "Function 'slow_func' took" in captured.out

def test_decorator_with_parens_timing(capsys):
    @Timing()
    def slow_func_parens(x):
        time.sleep(0.01)
        return x * 2

    result = slow_func_parens(5)
    assert result == 10
    
    captured = capsys.readouterr()
    assert "Function 'slow_func_parens' took" in captured.out

def test_direct_call_timing(capsys):
    def my_func(x):
        time.sleep(0.01)
        return x + 1
    
    timer = Timing(my_func)
    result = timer(10)
    assert result == 11
    assert timer.seconds >= 0.01
    
    captured = capsys.readouterr()
    assert "Function 'my_func' took" in captured.out

def test_is_running_states():
    timer = Timing()
    assert not timer.is_running
    timer.start()
    assert timer.is_running
    timer.stop()
    assert not timer.is_running
    timer.start()
    assert timer.is_running

def test_invalid_call():
    timer = Timing()
    with pytest.raises(TypeError, match="Timing doesn't support arguments."):
        timer(1, 2, 3)
