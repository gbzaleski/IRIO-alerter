from .types import MonitoredServiceInfo, ServiceId, MonitorId, MonitoredServicesLease
from . import queries
from .spanner import get_spanner_database
import os
from datetime import timedelta
import asyncio
from functools import partial
from google.cloud import spanner
from google.cloud.spanner_v1.database import Database
from google.cloud.spanner_v1.transaction import Transaction
from google.cloud.spanner_v1 import param_types


from typing import Union, Annotated

from fastapi import FastAPI, Query, Body, Path
from fastapi.responses import HTMLResponse

from pydantic import BaseModel

app = FastAPI()

ServiceId = str

database = get_spanner_database()

def fullrowToMonitoredServiceInfo(x):
    [sid, url, frequency, alertingWindow, allowedResponseTime] = x
    return {"serviceId": sid, "url": url, "frequency": frequency, "alertingWindow": alertingWindow, "allowedResponseTime": allowedResponseTime}

@app.post("/service")
async def service_insert(service: MonitoredServiceInfo):
    def f(transaction: Transaction):
        transaction.insert(
            "MonitoredServices",
            columns=["Url", "Frequency", "AlertingWindow", "AllowedResponseTime"],
            values=[
                [
                    service.url,
                    service.frequency,
                    service.alertingWindow,
                    service.allowedResponseTime
                ]
            ],
        )
    await asyncio.get_running_loop().run_in_executor(
        None, database.run_in_transaction, f,
    )
    return {"result": "OK"}

update_one_query = """
UPDATE MonitoredServices
SET Url = @Url,
Frequency = @Frequency,
AlertingWindow = @AlertingWindow,
AllowedResponseTime = @AllowedResponseTime
WHERE ServiceId = @ServiceId
"""
@app.put("/service")
async def service_update(service: MonitoredServiceInfo):
    def f(transaction: Transaction):
        transaction.execute_update(
            update_one_query,
            params={
                "ServiceId": service.serviceId,
                "Url": service.url,
                "Frequency": service.frequency,
                "AlertingWindow": service.alertingWindow,
                "AllowedResponseTime": service.allowedResponseTime
            },
            param_types={
                "ServiceId": param_types.STRING,
                "Url": param_types.STRING,
                "Frequency": param_types.INT64,
                "AlertingWindow": param_types.INT64,
                "AllowedResponseTime": param_types.INT64,
            },
        )
    await asyncio.get_running_loop().run_in_executor(
        None, database.run_in_transaction, f,
    )
    return {"result": "OK"}

delete_query = """
DELETE FROM MonitoredServices
WHERE ServiceId = @ServiceId
"""
@app.delete("/service/{serviceId}")
async def service_delete(serviceId: Annotated [ServiceId, Path(max_length=36)]):
    def f(transaction: Transaction):
        transaction.execute_update(
            delete_query,
            params={
                "ServiceId": serviceId
            },
            param_types={
                "ServiceId": param_types.STRING
            },
        )
    await asyncio.get_running_loop().run_in_executor(
        None, database.run_in_transaction, f,
    )
    return {"result": "OK"}

get_all_query = """
SELECT *
FROM MonitoredServices
"""
@app.get("/service/", response_model=list[MonitoredServiceInfo])
async def service_get_all():
    def f(transaction: Transaction, results):
        for x in transaction.execute_sql(get_all_query):
            results.append(fullrowToMonitoredServiceInfo(x))
    results = []
    await asyncio.get_running_loop().run_in_executor(
        None, database.run_in_transaction, f, results
    )
    return results

get_one_query = """
SELECT *
FROM MonitoredServices
WHERE ServiceId = @ServiceId
"""
@app.get("/service/{serviceId}", response_model=list[MonitoredServiceInfo])
async def service_get(serviceId: Annotated [ServiceId, Path(max_length=36)]):
    def f(transaction: Transaction, results):
        for x in transaction.execute_sql(
                get_one_query, 
                params = {
                    "ServiceId": serviceId
                },
                param_types={
                    "ServiceId": param_types.STRING
                }):
            results.append(fullrowToMonitoredServiceInfo(x))
    results = []
    await asyncio.get_running_loop().run_in_executor(
        None, database.run_in_transaction, f, results
    )
    return results

@app.get("/monitors/{monitor_id}/services/", response_model=list[MonitoredServicesLease])
def monitored_by(monitor_id: MonitorId):
    return queries.get_monitored_by(monitor_id)

@app.get('/monitors/', response_model=list[MonitorId])
def active_monitors():
    return queries.active_monitors()
