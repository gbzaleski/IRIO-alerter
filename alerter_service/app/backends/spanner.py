import os
import asyncio
from functools import partial
from google.cloud import spanner
from google.cloud.spanner_v1.database import Database
from google.cloud.spanner_v1.transaction import Transaction
from google.cloud.spanner_v1 import param_types
import structlog

from ..types import Alert, AlertId, AlertStatus, ServiceId, ContactMethod
from ..poller import AlertPoller, AlertPollerConfiguration
from ..sender import AlertStateManager

logger = structlog.stdlib.get_logger()


class AlertPollerSpanner(AlertPoller):
    def __init__(self, config: AlertPollerConfiguration, *, database: Database):
        super().__init__(config)
        self._database = database

    async def poll_alerts(self, alerts_limit: int):
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None,
            partial(
                _poll_alerts,
                database=self._database,
                limit=alerts_limit,
                config=self.config,
            ),
        )


class AlertStateManagerSpanner(AlertStateManager):
    def __init__(self, *, database: Database):
        self._database = database

    async def mark_alerts_as_sent(self, alerts: list[Alert]):
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None,
            partial(_mark_alerts_as_sent, database=self._database, alerts=alerts),
        )

    async def get_contact_methods_for_alerts(
        self, alerts: list[Alert]
    ) -> dict[AlertId, ContactMethod]:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None,
            partial(
                _get_contact_methods_for_alerts, database=self._database, alerts=alerts
            ),
        )


GET_ALERTS_SQL = f"""
SELECT AlertId, ServiceId, DetectionTimestamp, AlertStatus
FROM Alerts
WHERE ShardId IN UNNEST(@CoveredShards)
AND (AlertStatus = {AlertStatus.SUBMITTED.value} OR AlertStatus = {AlertStatus.NOTIFY1.value})
    AND (StatusExpirationTimestamp IS NULL OR StatusExpirationTimestamp < CURRENT_TIMESTAMP())
LIMIT @Limit
"""

LEASE_ALERTS_SQL = """
UPDATE Alerts
SET
StatusExpirationTimestamp = TIMESTAMP_MILLIS(UNIX_MILLIS(CURRENT_TIMESTAMP()) + @LeaseDurationMs)
WHERE AlertId IN UNNEST(@AlertsIds)
"""


def _poll_alerts(
    database: Database, limit: int, config: AlertPollerConfiguration
) -> list[Alert]:
    def f(transaction: Transaction):
        r = list(
            transaction.execute_sql(
                GET_ALERTS_SQL,
                params={"Limit": limit, "CoveredShards": list(config.covered_shards)},
                param_types={
                    "Limit": param_types.INT64,
                    "CoveredShards": param_types.Array(param_types.INT64),
                },
            )
        )
        transaction.execute_update(
            LEASE_ALERTS_SQL,
            params={
                "LeaseDurationMs": config.lease_duration,
                "AlertsIds": [x[0] for x in r],
            },
            param_types={
                "LeaseDurationMs": param_types.INT64,
                "AlertsIds": param_types.Array(param_types.STRING),
            },
        )
        return [
            Alert(
                alertId=x[0],
                serviceId=x[1],
                detectionTimestamp=x[2],
                status=AlertStatus(x[3]),
            )
            for x in r
        ]

    return database.run_in_transaction(f)


GET_SERVICES_AllowedResponseTime_SQL = """
SELECT ServiceId, AllowedResponseTime
FROM MonitoredServices
WHERE ServiceId IN UNNEST(@ServicesIds)
"""


def _get_services_allowed_response_time(
    transaction: Transaction, services_ids: list[ServiceId]
):
    r = transaction.execute_sql(
        GET_SERVICES_AllowedResponseTime_SQL,
        params={"ServicesIds": services_ids},
        param_types={"ServicesIds": param_types.Array(param_types.STRING)},
    )
    return r.to_dict_list()


MARK_ALERT_AS_SENT_SQL = f"""
UPDATE Alerts
SET AlertStatus = AlertStatus + 1,
StatusExpirationTimestamp = TIMESTAMP_MILLIS(UNIX_MILLIS(CURRENT_TIMESTAMP()) + @ExpireTimeMs)
WHERE AlertId = @AlertId
AND (AlertStatus = {AlertStatus.SUBMITTED.value} OR AlertStatus = {AlertStatus.NOTIFY1.value})
"""


def _mark_alerts_as_sent(database: Database, alerts: list[Alert]):
    def f(transaction: Transaction):
        _begin_transaction(transaction)

        service_id_to_allowed_response_time = {
            x["ServiceId"]: x["AllowedResponseTime"]
            for x in _get_services_allowed_response_time(
                transaction, [alert.serviceId for alert in alerts]
            )
        }
        pt = {"AlertId": param_types.STRING, "ExpireTimeMs": param_types.INT64}
        statements = [
            (
                MARK_ALERT_AS_SENT_SQL,
                {
                    "AlertId": alert.alertId,
                    "ExpireTimeMs": service_id_to_allowed_response_time[
                        alert.serviceId
                    ],
                },
                pt,
            )
            for alert in alerts
        ]
        r = transaction.batch_update(statements)

    database.run_in_transaction(f)


GET_SERVICES_CONTACT_METHODS_SQL = """
SELECT ServiceId, MethodOrder, Email
FROM ContactMethods
WHERE ServiceId IN UNNEST(@ServicesIds)
"""


def _get_contact_methods_for_alerts(database: Database, alerts: list[Alert]):
    def f(transaction: Transaction):
        r = {
            (service, order): email
            for service, order, email in transaction.execute_sql(
                GET_SERVICES_CONTACT_METHODS_SQL,
                params={"ServicesIds": [alert.serviceId for alert in alerts]},
                param_types={"ServicesIds": param_types.Array(param_types.STRING)},
            )
        }
        contact_methods = {}
        for alert in alerts:
            match alert.status:
                case AlertStatus.SUBMITTED:
                    order = 0
                case AlertStatus.NOTIFY1:
                    order = 1
                case other:
                    logger.error(
                        f"Invalid alert ({alert.alertId}) status {other}",
                        alertId=alert.alertId,
                        alert_status=other.value,
                    )

            method = r.get((alert.serviceId, order))
            if method is None:
                logger.error(
                    f"No contact method for alert ({alert.alertId}) status {alert.status}",
                    alertId=alert.alertId,
                    alert_status=alert.status.value,
                )
            else:
                contact_methods[alert.alertId] = ContactMethod(email=method)
        return contact_methods

    return database.run_in_transaction(f)


def _begin_transaction(transaction: Transaction):
    if transaction._transaction_id is None:
        transaction.begin()


def get_spanner_database():
    PROJECT_ID = os.environ.get("PROJECT_ID", "test-project")
    INSTANCE_NAME = os.environ.get("INSTANCE_NAME", "test-instance")
    DATABASE_NAME = os.environ.get("DATABASE_NAME", "test-database")

    client = spanner.Client(PROJECT_ID)
    instance = client.instance(INSTANCE_NAME)
    db = instance.database(DATABASE_NAME)
    return db
