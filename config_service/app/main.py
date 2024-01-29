from .types import (
    MonitoredServiceInfo,
    ServiceId,
    MonitorId,
    AlerterId,
    MonitoredServicesLease,
    Alert,
    ContactMethod,
    MonitoredServiceInsertRequest,
    MonitoredServiceInsertResponse,
    ActiveMonitor,
    MonitoredServiceUpdateRequest,
)
from . import queries

from typing import Annotated
from pydantic import ValidationError

from fastapi import FastAPI, Query, Body, Path
from fastapi.responses import HTMLResponse
from datetime import datetime


app = FastAPI()


@app.post("/service/", response_model=MonitoredServiceInsertResponse)
def service_insert(service: MonitoredServiceInsertRequest):
    return queries.insert_service(service)


@app.put("/service/{serviceId}/")
def service_update(
    serviceId: Annotated[ServiceId, Path(max_length=36)],
    service: MonitoredServiceUpdateRequest,
):
    return queries.update_service(serviceId, service)


@app.delete("/service/{serviceId}/")
def service_delete(serviceId: Annotated[ServiceId, Path(max_length=36)]):
    return queries.delete_service(serviceId)


@app.get("/service/", response_model=list[MonitoredServiceInfo])
def service_get_all():
    return queries.get_services_info()


@app.get("/service/{serviceId}/", response_model=list[MonitoredServiceInfo])
def service_get(serviceId: Annotated[ServiceId, Path(max_length=36)]):
    return queries.get_service(serviceId)


@app.get("/service/{serviceId}/monitors/", response_model=list[MonitoredServicesLease])
def service_monitors(serviceId: Annotated[ServiceId, Path(max_length=36)]):
    return queries.get_service_monitors(serviceId)


@app.get("/service/{serviceId}/contact_methods/", response_model=list[ContactMethod])
def service_contact_methods(serviceId: Annotated[ServiceId, Path(max_length=36)]):
    return queries.get_service_contact_methods(serviceId)


@app.put("/service/{serviceId}/contact_methods/")
def service_change_contact_methods(
    serviceId: Annotated[ServiceId, Path(max_length=36)],
    contact_methods: list[ContactMethod],
):
    if len(contact_methods) != 2:
        raise ValidationError("Service needs to have exactly 2 contact methods")

    queries.replace_service_contact_methods(serviceId, contact_methods)


@app.get(
    "/monitors/{monitor_id}/services/", response_model=list[MonitoredServicesLease]
)
def monitored_by(monitor_id: Annotated[MonitorId, Path(max_length=36)]):
    return queries.get_monitored_by(monitor_id)


@app.get("/monitors/", response_model=list[ActiveMonitor])
def active_monitors():
    return queries.active_monitors()


@app.post("/alerts/{alertId}/ack/")
def alert_ack(alertId: AlerterId):
    return queries.ack_alert(alertId)


@app.get("/alerts/{alertId}/", response_model=Alert | None)
def alert_status(alertId: AlerterId):
    return queries.alert_status(alertId)


@app.get("/service/{serviceId}/alerts/", response_model=list[Alert])
def service_alerts(serviceId: ServiceId):
    return queries.get_service_alerts(serviceId)


@app.post("/ack/{serviceId}/{detectionTimestamp}")
def service_ack(
    serviceId: Annotated[ServiceId, Path(max_length=36)], detectionTimestamp: datetime
):
    return queries.ack_service(serviceId, detectionTimestamp)


@app.post("/tests/delete_all/")
def tests_delete_all():
    queries.delete_all_services()
