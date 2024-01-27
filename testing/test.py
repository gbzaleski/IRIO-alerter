import requests
import json
from pprint import pprint
from functools import wraps
import time

def timeit(n):
    def decorator(func):
        @wraps(func)
        def timeit_wrapper(*args, **kwargs):
            start_time = time.perf_counter()
            for _ in range(n):
                result = func(*args, **kwargs)
            end_time = time.perf_counter()
            total_time = end_time - start_time
            print(f'Function {func.__name__} ran {n} times and took {total_time:.4f} seconds, {total_time/n:.4f} per call')
            return result
        return timeit_wrapper
    return decorator

N = 12

@timeit(N)
def call_time(url):
    response_API = requests.get(url)

def call_print(url):
    print(url)
    response_API = requests.get(url)
    print(response_API.status_code)
    result = json.loads(response_API.text)
    pprint(result)

def zip_call(url):
    call_print(url)
    call_time(url)

if __name__ == "__main__":
    main_url = "http://104.154.246.19:8000/"
    url_service = f"{main_url}service/"
    zip_call(url_service)

    url_monitor = f"{main_url}monitors/"
    zip_call(url_monitor)