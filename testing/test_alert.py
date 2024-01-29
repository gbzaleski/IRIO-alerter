import pytest
import requests
import os
import time
import logging
from .settings import MAIN_URL
from .types import Alert, ServiceId, AlertStatus, AlerterId

TIMEOUT = 5.0


def clear_environment():
    r = requests.post(f"{MAIN_URL}tests/delete_all/", timeout=TIMEOUT)
    assert r.status_code == 200


@pytest.fixture()
def clear_environment_fixture():
    clear_environment()
    yield
    clear_environment()


def insert_service(data) -> ServiceId:
    r = requests.post(f"{MAIN_URL}service/", json=data, timeout=TIMEOUT)
    assert r.status_code == 200
    return r.json()["serviceId"]


def get_service_alerts(serviceId: str) -> list[Alert]:
    r = requests.get(f"{MAIN_URL}service/{serviceId}/alerts/", timeout=TIMEOUT)
    assert r.status_code == 200
    return [Alert.model_validate(x) for x in r.json()]


def ack_alert(alertId: AlerterId):
    r = requests.post(f"{MAIN_URL}alerts/{alertId}/ack/", timeout=TIMEOUT)
    assert r.status_code == 200


def sleep(s: float):
    logging.info(f"Sleeping for {s // 60:.0f} min {s % 60:.0f} s")
    time.sleep(s)


def monitor_inserts_alert_for_unresponding_service(serviceId: ServiceId):
    logging.info(f"testing: monitor_inserts_alert_for_unresponding_service {serviceId}")
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


def alerter_sends_alert_to_first_admin(serviceId: ServiceId):
    logging.info(f"testing: alerter_sends_alert_to_first_admin {serviceId}")
    first_admin_notified = None
    for i in range(8):
        alerts = get_service_alerts(serviceId)
        assert len(alerts) == 1
        alert = alerts[0]
        if alert.status == AlertStatus.NOTIFY1:
            first_admin_notified = i + 1
            break
        logging.info(f"Waiting for alerter. Sleeping for the {i+1}th time")
        sleep(10.0)

    assert first_admin_notified is not None
    logging.info(f"Found alert notification after {first_admin_notified} attempts")


def ensure_alert_status(alertId: AlerterId, serviceId: ServiceId, status: AlertStatus):
    alerts = get_service_alerts(serviceId)
    alert = [a for a in alerts if a.alertId == alertId][0]
    assert alert.status == status


def alert_is_ack_after_ack_by_admin(serviceId: ServiceId):
    alerts = get_service_alerts(serviceId)
    assert len(alerts) >= 1
    alert = alerts[0]
    ack_alert(alert.alertId)
    ensure_alert_status(alert.alertId, serviceId, AlertStatus.ACK)
    logging.info(
        f"Waiting some time to ensure that monitors/alerters do not modify ACKed alert"
    )
    sleep(120.0)
    ensure_alert_status(alert.alertId, serviceId, AlertStatus.ACK)


def test_monitor_alerter_admin_workflow(caplog, clear_environment_fixture):
    caplog.set_level(logging.INFO)

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
    monitor_inserts_alert_for_unresponding_service(serviceId)
    alerter_sends_alert_to_first_admin(serviceId)
    alert_is_ack_after_ack_by_admin(serviceId)


def test_monitor_does_not_insert_alert_for_properly_working_service(
    caplog, clear_environment_fixture
):
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
