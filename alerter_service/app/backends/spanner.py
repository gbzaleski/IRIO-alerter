import os
from datetime import timedelta
import logging
import asyncio
from functools import partial
from google.cloud import spanner
from google.cloud.spanner_v1.database import Database
from google.cloud.spanner_v1.transaction import Transaction
from google.cloud.spanner_v1 import param_types

from alerter_service.app.poller import AlertPollerConfiguration

from ..poller import AlertPoller
from ..types import Alert, AlertStatus


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


GET_ALERTS_SQL = f"""
SELECT AlertId, ServiceId, DetectionTimestamp, AlertStatus
FROM Alerts
WHERE ShardId IN UNNEST(@CoveredShards)
AND (AlertStatus = {AlertStatus.SUBMITTED.value} OR (AlertStatus = {AlertStatus.NOTIFY1.value}
    AND StatusExpirationTimestamp < CURRENT_TIMESTAMP()))
LIMIT @Limit
"""

LEASE_ALERTS_SQL = """
UPDATE Alerts
SET AlertStatus = AlertStatus + 1,
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
                params={
                    "Limit": limit,
                    "CoveredShards": list(config.covered_shards)
                },
                param_types={
                    "Limit": param_types.INT64,
                    "CoveredShards": param_types.Array(param_types.INT64)
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
                status=AlertStatus[x[3]],
            )
            for x in r
        ]

    return database.run_in_transaction(f)


def get_spanner_database():
    PROJECT_ID = os.environ.get("PROJECT_ID", "test-project")
    INSTANCE_NAME = os.environ.get("INSTANCE_NAME", "test-instance")
    DATABASE_NAME = os.environ.get("DATABASE_NAME", "test-database")

    client = spanner.Client(PROJECT_ID)
    instance = client.instance(INSTANCE_NAME)
    db = instance.database(DATABASE_NAME)
    return db
