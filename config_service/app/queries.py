from google.cloud.spanner_v1 import param_types
from google.cloud.spanner_v1.transaction import Transaction
from datetime import datetime

from .spanner import get_spanner_database
from .types import MonitoredServiceInfo, MonitorId, ServiceId, MonitoredServicesLease
from .common.types import AlertStatus

db = get_spanner_database()

ACK_SERVICE_SQL = """
UPDATE Alerts
SET AlertStatus = @Ack
WHERE ShardId = @ShardId 
AND ServiceId = @ServiceId 
AND DetectionTimestamp = @DetectionTimestamp
THEN RETURN ServiceId
"""

def ack_service(shardId: int, serviceId: ServiceId, detectionTimestamp: datetime):
    def f(transaction: Transaction, results):
        for x in transaction.execute_sql(
            ACK_SERVICE_SQL,
            params = {
                "ShardId": shardId,
                "ServiceId": serviceId,
                "DetectionTimestamp": detectionTimestamp,
                "Ack": AlertStatus.ACK.value
            },
            param_types={
                "ShardId": param_types.INT64,
                "ServiceId": param_types.STRING,
                "DetectionTimestamp": param_types.TIMESTAMP,
                "Ack": param_types.INT64
            }
            ):
            results.append(x)
    results = []
    db.run_in_transaction(f, results)
    return {"result": results}

def insert_service(service: MonitoredServiceInfo):
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
    db.run_in_transaction(f)
    return {"result": "OK"}

UPDATE_SERVICE_SQL = """
UPDATE MonitoredServices
SET Url = @Url,
Frequency = @Frequency,
AlertingWindow = @AlertingWindow,
AllowedResponseTime = @AllowedResponseTime
WHERE ServiceId = @ServiceId
"""

def update_service(service: MonitoredServiceInfo):
    def f(transaction: Transaction):
        transaction.execute_update(
            UPDATE_SERVICE_SQL,
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
    db.run_in_transaction(f)
    return {"result": "OK"}


DELETE_SERVICE_SQL = """
DELETE FROM MonitoredServices
WHERE ServiceId = @ServiceId
"""
def delete_service(serviceId: ServiceId):
    def f(transaction: Transaction):
        transaction.execute_update(
            DELETE_SERVICE_SQL,
            params={
                "ServiceId": serviceId
            },
            param_types={
                "ServiceId": param_types.STRING
            },
        )
    db.run_in_transaction(f)
    return {"result": "OK"}


GET_SERVICE_SQL = """
SELECT *
FROM MonitoredServices
WHERE ServiceId = @ServiceId
"""
def get_service(serviceId: ServiceId):
    with db.snapshot() as snapshot:
        results = snapshot.execute_sql(
                GET_SERVICE_SQL, 
                params = {
                    "ServiceId": serviceId
                },
                param_types={
                    "ServiceId": param_types.STRING
                })
    return [
        MonitoredServiceInfo(
            serviceId=x[0],
            url=x[1],
            frequency=x[2],
            alertingWindow=x[3],
            allowedResponseTime=x[4],
        )
        for x in results
    ]

GET_SERVICES_INFO_SQL = """
SELECT ServiceId, Url, Frequency, AlertingWindow, AllowedResponseTime
FROM MonitoredServices
"""
def get_services_info():
    with db.snapshot() as snapshot:
        results = snapshot.execute_sql(GET_SERVICES_INFO_SQL)

    return [
        MonitoredServiceInfo(
            serviceId=x[0],
            url=x[1],
            frequency=x[2],
            alertingWindow=x[3],
            allowedResponseTime=x[4],
        )
        for x in results
    ]


GET_MONITORED_BY_SQL = """
SELECT ServiceId, MonitorId, LeasedAt, LeasedTo FROM MonitoredServicesLease
WHERE MonitorId = @MonitorId AND LeasedTo > CURRENT_TIMESTAMP()
"""

ACTIVE_MONITORS_SQL = """
SELECT MonitorId FROM MonitoredServicesLease
WHERE LeasedTo > CURRENT_TIMESTAMP()
"""


def get_monitored_by(monitor_id: MonitorId) -> list[MonitoredServicesLease]:
    with db.snapshot() as snapshot:
        results = snapshot.execute_sql(
            GET_MONITORED_BY_SQL,
            params={
                "MonitorId": monitor_id,
            },
            param_types={"MonitorId": param_types.STRING},
        )
        return [
            MonitoredServicesLease(
                serviceId=x[0], monitorId=x[1], leasedAt=x[2], leasedTo=x[3]
            )
            for x in results
        ]


def active_monitors() -> list[MonitorId]:
    with db.snapshot() as snapshot:
        results = snapshot.execute_sql(ACTIVE_MONITORS_SQL)
        return [x[0] for x in results]
