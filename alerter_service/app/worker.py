import asyncio
import logging
from .backends.spanner import (
    get_spanner_database,
    AlertPollerSpanner,
    AlertStateManagerSpanner,
)

from .sender import (
    AlertSenderManager,
    AlertSenderManagerConfiguration,
    AlertSenderConfiguration,
)
from .settings import Settings
from .manager import WorkManager


def main(settings: Settings):
    logging.info("Starting alerter worker %s", settings.alerter_id)

    database = get_spanner_database()
    alerter_id = settings.alerter_id
    alert_poller = AlertPollerSpanner(
        config=settings.poller_config,
        database=database,
    )
    alert_sender_config = AlertSenderConfiguration(alerter_id=alerter_id)
    if settings.use_real_sender:
        from .backends.email import AlertSenderEmail

        alert_sender = AlertSenderEmail(alert_sender_config)
    else:
        from .backends.dummy import AlertSenderDummy

        alert_sender = AlertSenderDummy(alert_sender_config)

    alert_sender_manager = AlertSenderManager(
        config=AlertSenderManagerConfiguration(alerter_id=alerter_id),
        alert_sender=alert_sender,
        alert_state_manager=AlertStateManagerSpanner(database=database),
    )
    work_manager = WorkManager(
        config=settings.work_manager_config,
        alert_poller=alert_poller,
        alert_sender_manager=alert_sender_manager,
    )

    loop = asyncio.get_event_loop()
    loop.run_until_complete(work_manager.start())
