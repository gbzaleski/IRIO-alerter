from google.cloud.spanner_v1 import param_types

from .spanner import get_spanner_database
from .types import MonitoredServiceInfo, MonitorId, ServiceId, MonitoredServicesLease

db = get_spanner_database()

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
