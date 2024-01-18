from time import perf_counter

def get_time() -> float:
    return perf_counter()


def time_difference_in_ms(t1: float, t2: float) -> int:
    return int((t2 - t1) * 1000)