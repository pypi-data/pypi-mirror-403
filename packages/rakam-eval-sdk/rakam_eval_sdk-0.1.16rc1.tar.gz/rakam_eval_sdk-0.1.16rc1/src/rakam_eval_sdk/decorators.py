
import time
import os
import psutil
import functools


def eval_run(*dargs, **dkwargs):
    def wrapper(func):
        @functools.wraps(func)
        def inner(*args, **kwargs):
            process = psutil.Process(os.getpid())

            # Start metrics
            start_time = time.perf_counter()
            start_cpu = process.cpu_times()
            start_mem = process.memory_info().rss

            try:
                result = func(*args, **kwargs)
                return result
            finally:
                # End metrics
                end_time = time.perf_counter()
                end_cpu = process.cpu_times()
                end_mem = process.memory_info().rss

                elapsed = end_time - start_time
                cpu_used = (
                    (end_cpu.user + end_cpu.system)
                    - (start_cpu.user + start_cpu.system)
                )
                mem_diff_mb = (end_mem - start_mem) / (1024 * 1024)

                print(
                    f"[eval_run] {func.__module__}.{func.__name__} | "
                    f"time={elapsed:.4f}s | "
                    f"cpu={cpu_used:.4f}s | "
                    f"mem_delta={mem_diff_mb:.2f}MB"
                )

        return inner

    return wrapper
