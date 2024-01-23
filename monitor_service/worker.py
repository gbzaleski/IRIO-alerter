import uuid
import asyncio
from .backends.spanner import get_spanner_database, AlerterSpanner, WorkPollerSpanner
from .manager import WorkManager, WorkManagerConfiguration
from .poller import WorkPollerConfiguration
from .alerter import AlerterConfiguration


def main():
    database = get_spanner_database()
    monitor_id = str(uuid.uuid4())
    work_poller = WorkPollerSpanner(
        config=WorkPollerConfiguration(
            monitor_id=monitor_id, lease_duration=30000, monitor_replication_factor=3
        ),
        database=database,
    )
    alerter = AlerterSpanner(
        config=AlerterConfiguration(alert_cooldown=120000), database=database
    )
    work_manager = WorkManager(
        config=WorkManagerConfiguration(monitor_id=monitor_id),
        work_poller=work_poller,
        alerter=alerter,
    )

    loop = asyncio.get_event_loop()
    loop.run_until_complete(work_manager.start())


if __name__ == "__main__":
    main()
