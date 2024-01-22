from .types import MonitoredServiceInfo, ServiceId, MonitorId, MonitoredServicesLease
from . import queries
import os
from datetime import timedelta
import asyncio
from functools import partial

from typing import Union, Annotated

from fastapi import FastAPI, Query, Body, Path
from fastapi.responses import HTMLResponse
from datetime import datetime

from pydantic import BaseModel

app = FastAPI()

ServiceId = str

@app.post("/service")
def service_insert(service: MonitoredServiceInfo):
    return queries.insert_service(service)

@app.put("/service")
def service_update(service: MonitoredServiceInfo): 
    return queries.update_service(service)

@app.delete("/service/{serviceId}")
def service_delete(serviceId: Annotated [ServiceId, Path(max_length=36)]):
    return queries.delete_service(serviceId) 

@app.get("/service/", response_model=list[MonitoredServiceInfo])
def service_get_all():
    return queries.get_services_info()

@app.get("/service/{serviceId}", response_model=list[MonitoredServiceInfo])
def service_get(serviceId: Annotated [ServiceId, Path(max_length=36)]):
    return queries.get_service(serviceId)
    
@app.get("/monitors/{monitor_id}/services/", response_model=list[MonitoredServicesLease])
def monitored_by(monitor_id: MonitorId):
    return queries.get_monitored_by(monitor_id)

@app.get('/monitors/', response_model=list[MonitorId])
def active_monitors():
    return queries.active_monitors()

@app.get('/ack/{shardId}/{serviceId}/{detectionTimestamp}')
def service_ack(shardId: int, serviceId: Annotated [ServiceId, Path(max_length=36)], detectionTimestamp: datetime):
    return queries.ack_service(shardId, serviceId, detectionTimestamp)
