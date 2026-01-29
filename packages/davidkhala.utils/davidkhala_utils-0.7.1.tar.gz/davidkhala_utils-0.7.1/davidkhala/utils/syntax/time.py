import time
from typing import Callable, Any


def runtime_of(func:Callable[[], Any]) -> tuple[float, Any]:
    assert callable(func)
    start_time = time.time()
    r = func()
    return time.time() - start_time, r


