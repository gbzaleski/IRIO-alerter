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
            assert total_time/n < 1.0
            return result
        return timeit_wrapper
    return decorator

N = 100
# Get time test
@timeit(N)
def call_time(url):
    response_API = requests.get(url)

# Get correctness test
def call_get(url, print_result = False):
    print("\n#################")
    print(url, "GET")
    response_API = requests.get(url)
    print(response_API.status_code)
    result = json.loads(response_API.text)
    
    if print_result:
        pprint(result)

    assert response_API.status_code == 200
    return result

# Insert correctness test
def call_post(url, data):
    print("\n#################")
    print(url, "POST")
    response_API = requests.post(url, json=data)
    print(response_API.status_code)
    result = json.loads(response_API.text)
    pprint(result)

    assert response_API.status_code == 200
    return result

# Update correctness test
def call_put_service(url, data):
    print("\n#################")
    print(url, "PUT")
    response_API = requests.put(url, json=data)
    print(response_API.status_code)
    result = json.loads(response_API.text)
    pprint(result)

    assert response_API.status_code == 200
    return result

# Delete correctness test
def delete_service(url):
    print("\n#################")
    print(url, "DEL")
    response_API = requests.delete(url)
    print(response_API.status_code)
    result = json.loads(response_API.text)
    pprint(result)

    assert response_API.status_code == 200
    return result

if __name__ == "__main__":

    # Api data
    main_url = "http://104.154.246.19:8000/"
    url_service = f"{main_url}service/"
    url_monitor = f"{main_url}monitors/"

    # Mock alert data
    data = {
        "url": "https://martinez-alert.com/",
        "frequency": 2_500,
        "alertingWindow": 10_000,
        "allowedResponseTime": 120_000,
        "contact_methods": [
            {
            "email": "default1@example.com"
            },
            {
            "email": "default2@example.com"
            }
        ]
    }

    # Insert service
    id = call_post(url_service, data)
    data = {**data, **id, "frequency": 5000}
    service_id = id['serviceId']

    # Update service data
    url_givenservice = url_service + service_id + "/"
    call_put_service(url_givenservice, data)

    # Query service list
    call_get(url_service)

    # Get service data
    call_get(url_givenservice, True)

    contact_value = [
        {
            "email": "user@example.com"
        },
        {
            "email": "adm1n@gmail.com"
        }
    ]
    url_contacts = url_givenservice + "contact_methods/"

    # Add contact data
    call_put_service(url_contacts, contact_value)

    # Access contact data
    call_get(url_contacts, True)

    # Access alert list for given service
    url_alerts = url_service + service_id + "/alerts/"
    call_get(url_alerts)

    # Add alert
    alert_url = main_url + "ack/" + service_id + "/" + str(int(time.time()))
    call_post(alert_url, {})

    # Time-test API for monitors
    call_time(url_monitor)

    # Time-test API for services
    call_time(url_service)

    # Get alert list
    url_alertlist = url_givenservice + "alerts/"
    call_get(url_alertlist, True)

    # Get monitor list
    call_get(url_monitor, True)

    # Delete added service
    delete_service(url_givenservice)


