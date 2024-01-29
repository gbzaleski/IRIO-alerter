import pytest
import requests
import os
import time
import logging
from .settings import MAIN_URL
from .types import Alert, ServiceId

TIMEOUT = 2.0


def clear_environment():
    r = requests.post(f"{MAIN_URL}tests/delete_all/", timeout=TIMEOUT)
    assert r.status_code == 200


def insert_service(data) -> ServiceId:
    r = requests.post(f"{MAIN_URL}service/", json=data, timeout=TIMEOUT)
    assert r.status_code == 200
    return r.json()["serviceId"]


def get_service_alerts(serviceId: str) -> list[Alert]:
    r = requests.get(f"{MAIN_URL}service/{serviceId}/alerts/", timeout=TIMEOUT)
    assert r.status_code == 200
    return [Alert.model_validate(x) for x in r.json()]


def sleep(s: float):
    logging.info(f"Sleeping for {s // 60:.0f} min {s % 60:.0f} s")
    time.sleep(s)


def test_monitor_inserts_alert_for_unresponding_service(caplog):
    caplog.set_level(logging.INFO)
    clear_environment()
    # Mock alert data
    data = {
        "url": "https://martinez-alert.com/",
        "frequency": 10_000,
        "alertingWindow": 20_000,
        "allowedResponseTime": 120_000,
        "contact_methods": [
            {"email": "default1@example.com"},
            {"email": "default2@example.com"},
        ],
    }

    serviceId = insert_service(data)
    assert (len(get_service_alerts(serviceId))) == 0
    alert_found = None

    for i in range(12):
        alerts = get_service_alerts(serviceId)
        assert len(alerts) <= 1
        if len(alerts) == 1:
            alert_found = i + 1
            break
        logging.info(f"Waiting for monitor. Sleeping for the {i+1}th time")
        sleep(10.0)

    assert alert_found is not None
    logging.info(f"Found alert for service after {alert_found} attempts")


def test_monitor_does_not_insert_alert_for_properly_working_service(caplog):
    caplog.set_level(logging.INFO)
    clear_environment()
    # Mock alert data
    data = {
        "url": "https://example.com/",
        "frequency": 10_000,
        "alertingWindow": 20_000,
        "allowedResponseTime": 120_000,
        "contact_methods": [
            {"email": "default1@example.com"},
            {"email": "default2@example.com"},
        ],
    }

    serviceId = insert_service(data)
    sleep(120.0)
    assert (len(get_service_alerts(serviceId))) == 0
