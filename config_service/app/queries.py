from google.cloud.spanner_v1 import param_types
from google.cloud.spanner_v1.transaction import Transaction
from datetime import datetime

from .spanner import get_spanner_database
from .types import (
    Alert,
    ContactMethod,
    MonitoredServiceInfo,
    MonitorId,
    ServiceId,
    AlerterId,
    MonitoredServicesLease,
    MonitoredServiceInsertRequest,
    MonitoredServiceInsertResponse,
    MonitoredServiceUpdateRequest,
    ActiveMonitor,
)
from .common.types import AlertStatus

db = get_spanner_database()


def begin_transaction(transaction: Transaction):
    if transaction._transaction_id is None:
        transaction.begin()


ACK_SERVICE_SQL = """
UPDATE Alerts
SET AlertStatus = @Ack
WHERE ServiceId = @ServiceId 
AND DetectionTimestamp = @DetectionTimestamp
THEN RETURN ServiceId
"""


def ack_service(serviceId: ServiceId, detectionTimestamp: datetime):
    def f(transaction: Transaction):
        results = []
        begin_transaction(transaction)
        for x in transaction.execute_sql(
            ACK_SERVICE_SQL,
            params={
                "ServiceId": serviceId,
                "DetectionTimestamp": detectionTimestamp,
                "Ack": AlertStatus.ACK.value,
            },
            param_types={
                "ServiceId": param_types.STRING,
                "DetectionTimestamp": param_types.TIMESTAMP,
                "Ack": param_types.INT64,
            },
        ):
            results.append(x)
        return results

    return {"result": db.run_in_transaction(f)}


ACK_ALERT_SQL = """
UPDATE Alerts
SET AlertStatus = @Ack
WHERE AlertId = @AlertId
"""


def ack_alert(alertId: AlerterId):
    def f(transaction: Transaction):
        transaction.execute_update(
            ACK_ALERT_SQL,
            params={"AlertId": alertId, "Ack": AlertStatus.ACK.value},
            param_types={"AlertId": param_types.STRING, "Ack": param_types.INT64},
        )

    db.run_in_transaction(f)


INSERT_SERVICE_SQL = """
INSERT INTO MonitoredServices (WorkspaceId, Url, Frequency, AlertingWindow, AllowedResponseTime)
VALUES (@WorkspaceId, @Url, @Frequency, @AlertingWindow, @AllowedResponseTime)
THEN RETURN ServiceId
"""


def insert_service(
    service: MonitoredServiceInsertRequest,
) -> MonitoredServiceInsertResponse:
    def f(transaction: Transaction):
        begin_transaction(transaction)

        r = transaction.execute_sql(
            INSERT_SERVICE_SQL,
            params={
                "WorkspaceId": "my_workspace",  # TODO:
                "Url": str(service.url),
                "Frequency": service.frequency,
                "AlertingWindow": service.alertingWindow,
                "AllowedResponseTime": service.allowedResponseTime,
            },
            param_types={
                "WorkspaceId": param_types.STRING,
                "Url": param_types.STRING,
                "Frequency": param_types.INT64,
                "AlertingWindow": param_types.INT64,
                "AllowedResponseTime": param_types.INT64,
            },
        ).one()
        serviceId = r[0]
        _replace_service_contact_methods(
            transaction, serviceId, service.contact_methods
        )
        return MonitoredServiceInsertResponse(serviceId=serviceId)

    return db.run_in_transaction(f)


UPDATE_SERVICE_SQL = """
UPDATE MonitoredServices
SET Url = @Url,
Frequency = @Frequency,
AlertingWindow = @AlertingWindow,
AllowedResponseTime = @AllowedResponseTime
WHERE ServiceId = @ServiceId
"""


def update_service(serviceId: ServiceId, service: MonitoredServiceUpdateRequest):
    def f(transaction: Transaction):
        transaction.execute_update(
            UPDATE_SERVICE_SQL,
            params={
                "ServiceId": serviceId,
                "Url": str(service.url),
                "Frequency": service.frequency,
                "AlertingWindow": service.alertingWindow,
                "AllowedResponseTime": service.allowedResponseTime,
            },
            param_types={
                "ServiceId": param_types.STRING,
                "Url": param_types.STRING,
                "Frequency": param_types.INT64,
                "AlertingWindow": param_types.INT64,
                "AllowedResponseTime": param_types.INT64,
            },
        )
        _delete_service_leases(transaction, serviceId)

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
            params={"ServiceId": serviceId},
            param_types={"ServiceId": param_types.STRING},
        )
        _delete_service_leases(transaction, serviceId)

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
            params={"ServiceId": serviceId},
            param_types={"ServiceId": param_types.STRING},
        )
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
SELECT ServiceId, MonitorId, LeasedAt, LeasedTo
FROM MonitoredServicesLease
WHERE MonitorId = @MonitorId AND LeasedTo > CURRENT_TIMESTAMP()
"""

ACTIVE_MONITORS_SQL = """
SELECT MonitorId, MAX(LeasedTo) FROM MonitoredServicesLease
WHERE LeasedTo > CURRENT_TIMESTAMP()
GROUP BY MonitorId
"""

SERVICE_CONTACT_METHODS_SQL = """
SELECT Email FROM ContactMethods
WHERE ServiceId = @ServiceId
ORDER BY MethodOrder
"""

SERVICE_DELETE_CONTACT_METHODS_SQL = """
DELETE FROM ContactMethods
WHERE ServiceId = @ServiceId
"""


def get_service_contact_methods(serviceId: ServiceId) -> list[ContactMethod]:
    with db.snapshot() as snapshot:
        results = snapshot.execute_sql(
            SERVICE_CONTACT_METHODS_SQL,
            params={"ServiceId": serviceId},
            param_types={"ServiceId": param_types.STRING},
        )
        return [ContactMethod(email=x[0]) for x in results]


def _replace_service_contact_methods(
    transaction: Transaction, serviceId: ServiceId, contact_methods: list[ContactMethod]
):
    begin_transaction(transaction)
    transaction.execute_update(
        SERVICE_DELETE_CONTACT_METHODS_SQL,
        params={"ServiceId": serviceId},
        param_types={"ServiceId": param_types.STRING},
    )

    transaction.insert(
        "ContactMethods",
        ["ServiceId", "MethodOrder", "Email"],
        [(serviceId, i, x.email) for i, x in enumerate(contact_methods)],
    )


def replace_service_contact_methods(
    serviceId: ServiceId, contact_methods: list[ContactMethod]
):
    db.run_in_transaction(_replace_service_contact_methods, serviceId, contact_methods)


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


def active_monitors() -> list[ActiveMonitor]:
    with db.snapshot() as snapshot:
        results = snapshot.execute_sql(ACTIVE_MONITORS_SQL)
        return [
            ActiveMonitor(monitorId=monitorId, leasedTo=leasedTo)
            for monitorId, leasedTo in results
        ]


GET_SERVICE_ALERTS_SQL = """
SELECT AlertId, ServiceId, DetectionTimestamp, AlertStatus
FROM Alerts
WHERE ServiceId = @ServiceId
ORDER BY DetectionTimestamp DESC
"""


def get_service_alerts(serviceId: ServiceId) -> list[Alert]:
    with db.snapshot() as snapshot:
        results = snapshot.execute_sql(
            GET_SERVICE_ALERTS_SQL,
            params={"ServiceId": serviceId},
            param_types={"ServiceId": param_types.STRING},
        )

        return [
            Alert(
                alertId=x[0],
                serviceId=x[1],
                detectionTimestamp=x[2],
                status=AlertStatus(x[3]),
            )
            for x in results
        ]


def _delete_service_leases(transaction: Transaction, serviceId: ServiceId):
    begin_transaction(transaction)
    transaction.execute_update(
        "DELETE FROM MonitoredServicesLease WHERE ServiceId = @ServiceId",
        params={"ServiceId": serviceId},
        param_types={"ServiceId": param_types.STRING},
    )


def delete_all_services():
    def f(transaction: Transaction):
        begin_transaction(transaction)
        transaction.execute_update("DELETE FROM MonitoredServices WHERE 1=1")
        transaction.execute_update("DELETE FROM ContactMethods WHERE 1=1")
        transaction.execute_update("DELETE FROM MonitoredServicesLease WHERE 1=1")
        transaction.execute_update("DELETE FROM Alerts WHERE 1=1")

    print(db.run_in_transaction(f))
