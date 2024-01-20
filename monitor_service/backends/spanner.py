import os
from datetime import timedelta
import asyncio
from functools import partial
from google.cloud import spanner
from google.cloud.spanner_v1.database import Database
from google.cloud.spanner_v1.transaction import Transaction
from google.cloud.spanner_v1 import param_types

from monitor_service.types import (
    Miliseconds,
    MonitorId,
    MonitoredServiceInfo,
    ServiceId,
)
from ..alerter import Alert, AlertStatus, Alerter, ALERT_COOLDOWN
from ..poller import WorkPoller, WorkPollerConfiguration


LAST_SUBMITTED_ALERT_SQL = """
SELECT DetectionTimestamp, AlertStatus FROM Alerts
WHERE ServiceId = @ServiceId
ORDER BY DetectionTimestamp DESC
LIMIT 1
"""


class AlerterSpanner(Alerter):
    _database: Database

    def __init__(self, *, database: Database):
        self._database = database

    async def send_alert(self, alert: Alert):
        alert.timestamp = await self._get_timestamp()
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(
            None, partial(_send_alert, alert=alert, database=self._database)
        )

    async def _get_timestamp(self):
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, partial(_get_timestamp, self._database))


def _get_timestamp(database: Database):
    with database.snapshot() as snapshot:
        results = snapshot.execute_sql("SELECT CURRENT_TIMESTAMP() AS now")
        return results.one()[0]


def _send_alert(database: Database, alert: Alert):
    def f(transaction: Transaction):
        last_alert = transaction.execute_sql(
            LAST_SUBMITTED_ALERT_SQL,
            params={"ServiceId": alert.serviceId},
            param_types={"ServiceId": param_types.STRING},
        ).one_or_none()

        if last_alert is not None:
            millis = (alert.timestamp - last_alert[0]) / timedelta(milliseconds=1)
            if last_alert[1] != AlertStatus.SUBMITTED.value or millis < ALERT_COOLDOWN:
                return  # TODO: log

        transaction.insert(
            "Alerts",
            columns=["ServiceId", "MonitorId", "DetectionTimestamp", "AlertStatus"],
            values=[
                [
                    alert.serviceId,
                    alert.monitorId,
                    alert.timestamp,
                    AlertStatus.SUBMITTED.value,
                ]
            ],
        )

    database.run_in_transaction(f)


class WorkPollerSpanner(WorkPoller):
    def __init__(self, config: WorkPollerConfiguration, *, database: Database):
        super().__init__(config)
        self._database = database

    async def poll_for_work(
        self,
        new_services_limit: int,
        already_monitored_services: list[ServiceId],
    ) -> list[ServiceId]:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None,
            partial(
                _poll_for_work,
                database=self._database,
                new_services_limit=new_services_limit,
                already_monitored_services=already_monitored_services,
                config=self.config,
            ),
        )

    async def renew_lease(
        self,
        services: list[ServiceId],
    ) -> None:
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(
            None,
            partial(
                _renew_lease,
                database=self._database,
                services=services,
                config=self.config,
            ),
        )

    async def get_services_info(
        self, services: list[ServiceId]
    ) -> list[MonitoredServiceInfo]:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None,
            partial(_get_services_info, database=self._database, services=services),
        )


def _poll_for_work(
    database: Database,
    new_services_limit: int,
    already_monitored_services: list[ServiceId],
    config: WorkPollerConfiguration,
) -> list[ServiceId]:
    s = "6839b274-f5ab-42f5-a3f8-ea10bbf2b599"
    if s in already_monitored_services:
        return []

    # TODO: real implementation
    def f(transaction: Transaction):
        already_exists = transaction.execute_sql(
            "SELECT ServiceId FROM MonitoredServicesLease WHERE MonitorId = @MonitorId AND ServiceId = @ServiceId",
            params={
                "ServiceId": s,
                "MonitorId": config.monitor_id,
            },
            param_types={
                "ServiceId": param_types.STRING,
                "MonitorId": param_types.STRING
            },
        )
        if already_exists.one_or_none() is not None:
            return [s]

        transaction.execute_update(
            "INSERT INTO MonitoredServicesLease (ServiceId, MonitorId, LeasedAt, LeaseDurationMs) VALUES (@ServiceId, @MonitorId, PENDING_COMMIT_TIMESTAMP(), @LeaseDurationMs)",
            params={
                "ServiceId": s,
                "MonitorId": config.monitor_id,
                "LeaseDurationMs": config.lease_duration,
            },
            param_types={
                "ServiceId": param_types.STRING,
                "MonitorId": param_types.STRING,
                "LeaseDurationMs": param_types.INT64,
            },
        )

    database.run_in_transaction(f)
    return [s]


RENEW_LEASE_SQL = """
UPDATE MonitoredServicesLease
SET LeasedAt = PENDING_COMMIT_TIMESTAMP(),
LeaseDurationMs = @LeaseDurationMs
WHERE MonitorId = @MonitorId AND ServiceId IN UNNEST(@ServicesIds) 
"""


def _renew_lease(
    database: Database, services: list[ServiceId], config: WorkPollerConfiguration
):
    def f(transaction: Transaction):
        transaction.execute_sql(
            RENEW_LEASE_SQL,
            params={
                "LeaseDurationMs": config.lease_duration,
                "MonitorId": config.monitor_id,
                "ServicesIds": services,
            },
            param_types={
                "LeaseDurationMs": param_types.INT64,
                "MonitorId": param_types.STRING,
                "ServicesIds": param_types.Array(param_types.STRING),
            },
        )

    database.run_in_transaction(f)


GET_SERVICES_INFO_SQL = """
SELECT ServiceId, Url, Frequency, AlertingWindow, AllowedResponseTime
FROM MonitoredServices
WHERE ServiceId IN UNNEST(@ServicesIds)
"""


def _get_services_info(database: Database, services: list[ServiceId]):
    with database.snapshot() as snapshot:
        results = snapshot.execute_sql(
            GET_SERVICES_INFO_SQL,
            params={"ServicesIds": services},
            param_types={"ServicesIds": param_types.Array(param_types.STRING)},
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


def get_spanner_database():
    PROJECT_ID = os.environ.get("PROJECT_ID", "test-project")
    INSTANCE_NAME = os.environ.get("INSTANCE_NAME", "test-instance")
    DATABASE_NAME = os.environ.get("DATABASE_NAME", "test-database")

    client = spanner.Client(PROJECT_ID)
    instance = client.instance(INSTANCE_NAME)
    db = instance.database(DATABASE_NAME)
    return db


def _get_alerts(database: Database):
    with database.snapshot() as snapshot:
        results = snapshot.execute_sql("SELECT * FROM Alerts")
        return results.to_dict_list()


async def get_alerts(database: Database):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, partial(_get_alerts, database))
