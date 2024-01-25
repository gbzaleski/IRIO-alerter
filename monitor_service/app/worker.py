import asyncio
import structlog
from .backends.spanner import get_spanner_database, AlerterSpanner, WorkPollerSpanner
from .manager import WorkManager
from .settings import Settings

logger = structlog.stdlib.get_logger()


def main(settings: Settings):
    logger.info("Starting monitor worker", monitor_id=settings.monitor_id)
    database = get_spanner_database()
    work_poller = WorkPollerSpanner(
        config=settings.poller_config,
        database=database,
    )
    alerter = AlerterSpanner(config=settings.alerter_config, database=database)
    work_manager = WorkManager(
        config=settings.work_manager_config,
        work_poller=work_poller,
        alerter=alerter,
    )

    loop = asyncio.get_event_loop()
    loop.run_until_complete(work_manager.start())
