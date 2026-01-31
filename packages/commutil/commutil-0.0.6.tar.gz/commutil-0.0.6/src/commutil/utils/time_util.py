from datetime import datetime
import time
import functools

def get_now(mid="_"):
    return datetime.now().strftime(f"%Y-%m-%d{mid}%H-%M-%S")

def timer(func):
    """
    A decorator to measure the execution time of a function.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        execution_time = end_time - start_time
        print(f"Function '{func.__name__}' executed in {execution_time:.4f} seconds")
        return result
    return wrapper
