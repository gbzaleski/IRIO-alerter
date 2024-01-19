import os
from datetime import timedelta, datetime
import asyncio
from functools import partial
import uuid
from google.cloud import spanner
from google.cloud.spanner_v1.database import Database
from google.cloud.spanner_v1.transaction import Transaction
from google.cloud.spanner_v1 import param_types
from ..alerter import Alert, AlertStatus, ALERT_COOLDOWN


LAST_SUBMITTED_ALERT_SQL = """
SELECT DetectionTimestamp, AlertStatus FROM Alerts
WHERE ServiceId = @ServiceId
ORDER BY DetectionTimestamp DESC
LIMIT 1
"""


class AlerterSpanner:
    _database: Database

    def __init__(self, database: Database):
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
    database.run_in_transaction(partial(_send_alert_transaction, alert=alert))


def _send_alert_transaction(transaction: Transaction, alert: Alert):
    last_alert = transaction.execute_sql(
        LAST_SUBMITTED_ALERT_SQL,
        params={"ServiceId": alert.serviceId},
        param_types={"ServiceId": param_types.STRING},
    ).one_or_none()

    if last_alert is not None:
        millis = (alert.timestamp - last_alert[0]) / timedelta(milliseconds=1)
        if last_alert[1] != AlertStatus.SUBMITTED.value or millis < ALERT_COOLDOWN:
            return #TODO: log

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


class WorkPollerSpanner:
    async def poll_for_work(self, new_services_limit: int, already_monitored_services):
        pass  # TODO:


async def test():
    PROJECT_ID = os.environ.get("PROJECT_ID", "test-project")
    INSTANCE_NAME = os.environ.get("INSTANCE_NAME", "test-instance")
    DATABASE_NAME = os.environ.get("DATABASE_NAME", "test-database")

    MONITOR_ID = str(uuid.uuid4())
    client = spanner.Client(PROJECT_ID)
    instance = client.instance(INSTANCE_NAME)
    db = instance.database(DATABASE_NAME)

    alerter = AlerterSpanner(db)
    # res = await alerter._get_timestamp()
    # print(res)
    await alerter.send_alert(
        Alert(
            serviceId="d45dce1c-2835-43b8-8fbc-c808e8a26a1d",
            monitorId=MONITOR_ID,
            timestamp=datetime.now(),
        )
    )

    res = await get_alerts(db)
    print(res)


def _get_alerts(database: Database):
    with database.snapshot() as snapshot:
        results = snapshot.execute_sql("SELECT * FROM Alerts")
        return results.to_dict_list()


async def get_alerts(database: Database):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, partial(_get_alerts, database))


if __name__ == "__main__":
    test()
