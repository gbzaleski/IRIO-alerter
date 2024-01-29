import asyncio
import signal
from pydantic import BaseModel
import structlog
from structlog.contextvars import bind_contextvars


from .types import Alert, AlerterId
from .poller import AlertPoller
from .sender import AlertSenderManager

logger = structlog.stdlib.get_logger()


class WorkManagerConfiguration(BaseModel):
    alerter_id: AlerterId
    alerts_batch_limit: int = 100
    alerts_poll_interval: float = 10.0  # TODO:


class WorkManager:
    def __init__(
        self,
        config: WorkManagerConfiguration,
        *,
        alert_poller: AlertPoller,
        alert_sender_manager: AlertSenderManager,
    ):
        self.config = config
        self._alert_poller = alert_poller
        self._alert_sender_manager = alert_sender_manager
        self.running = True
        signal.signal(signal.SIGINT, self._shutdown_gracefully)
        signal.signal(signal.SIGTERM, self._shutdown_gracefully)

    async def start(self):
        bind_contextvars(alerterId=self.config.alerter_id)
        await self._poll_alerts()

    async def _poll_alerts(self):
        while self.running:
            logger.info("Polling alerts")

            alerts = await self._alert_poller.poll_alerts(
                self.config.alerts_batch_limit
            )

            logger.info(
                f"New alerts to process {len(alerts)}", new_alerts_count=len(alerts)
            )
            await asyncio.gather(
                self._send_alerts(alerts),
                asyncio.sleep(self.config.alerts_poll_interval),
            )
            # TODO: log if can't keep up

    async def _send_alerts(self, alerts: list[Alert]):
        await self._alert_sender_manager.send_alerts(alerts)

    def _shutdown_gracefully(self, signum, frame):
        logger.info("Received shutdown signal %d", signum)
        self.running = False
