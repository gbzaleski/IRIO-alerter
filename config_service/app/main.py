from fastapi import FastAPI
from .types import MonitoredServiceInfo, ServiceId, MonitorId, MonitoredServicesLease
from . import queries

app = FastAPI()


@app.get("/")
async def read_root():
    return {"Hello": "World"}


@app.get("/services/", response_model=list[MonitoredServiceInfo])
def services():
    return queries.get_services_info()


@app.get("/monitors/{monitor_id}/services/", response_model=list[MonitoredServicesLease])
def monitored_by(monitor_id: MonitorId):
    return queries.get_monitored_by(monitor_id)

@app.get('/monitors/', response_model=list[MonitorId])
def active_monitors():
    return queries.active_monitors()