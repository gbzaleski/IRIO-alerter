import logging
import asyncio
from pydantic import BaseModel
from .types import Alert, AlerterId
from .poller import AlertPoller
from .sender import AlertSenderManager


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
        alert_sender_manager: AlertSenderManager
    ):
        self.config = config
        self._alert_poller = alert_poller
        self._alert_sender_manager = alert_sender_manager

    async def start(self):
        await self._poll_alerts()

    async def _poll_alerts(self):
        while True:
            logging.info("Polling alerts")  # TODO:

            alerts = await self._alert_poller.poll_alerts(
                self.config.alerts_batch_limit
            )

            print("New alerts", alerts)  # TODO:
            await asyncio.gather(
                self._send_alerts(alerts),
                asyncio.sleep(self.config.alerts_poll_interval),
            )
            # TODO: log if can't keep up

    async def _send_alerts(self, alerts: list[Alert]):
        await self._alert_sender_manager.send_alerts(alerts)
