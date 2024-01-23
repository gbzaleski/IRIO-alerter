import uuid
import asyncio
from .backends.spanner import (
    get_spanner_database,
    AlertPollerSpanner,
    AlertStateManagerSpanner,
)
from .backends.dummy import AlertSenderDummy
from .sender import (
    AlertSenderManager,
    AlertSenderManagerConfiguration,
    AlertSenderConfiguration,
)
from .manager import WorkManager, WorkManagerConfiguration
from .poller import AlertPollerConfiguration


def main():
    database = get_spanner_database()
    alerter_id = str(uuid.uuid4())
    alert_poller = AlertPollerSpanner(
        config=AlertPollerConfiguration(
            alerter_id=alerter_id, covered_shards=list(range(64)), lease_duration=10000
        ),
        database=database,
    )
    alert_sender_manager = AlertSenderManager(
        config=AlertSenderManagerConfiguration(alerter_id=alerter_id),
        alert_sender=AlertSenderDummy(
            config=AlertSenderConfiguration(alerter_id=alerter_id)
        ),
        alert_state_manager=AlertStateManagerSpanner(database=database),
    )
    work_manager = WorkManager(
        config=WorkManagerConfiguration(alerter_id=alerter_id),
        alert_poller=alert_poller,
        alert_sender_manager=alert_sender_manager,
    )

    loop = asyncio.get_event_loop()
    loop.run_until_complete(work_manager.start())


if __name__ == "__main__":
    main()
