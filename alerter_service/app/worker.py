import uuid
import asyncio
from .backends.spanner import get_spanner_database, AlertPollerSpanner
from .manager import WorkManager, WorkManagerConfiguration
from .poller import AlertPollerConfiguration


def main():
    database = get_spanner_database()
    alerter_id = str(uuid.uuid4())
    alert_poller = AlertPollerSpanner(
        config=AlertPollerConfiguration(alerter_id=alerter_id, covered_shards=list(range(64)), lease_duration=10000),
        database=database,
    )
    work_manager = WorkManager(
        config=WorkManagerConfiguration(alerter_id=alerter_id),
        alert_poller=alert_poller
    )

    loop = asyncio.get_event_loop()
    loop.run_until_complete(work_manager.start())

if __name__ == "__main__":
    main()