import logging
import asyncio
from pydantic import BaseModel
from .types import AlerterId
from .poller import AlertPoller


class WorkManagerConfiguration(BaseModel):
    alerter_id: AlerterId
    alerts_batch_limit: int = 100
    alerts_poll_interval: float = 10.0  # TODO:


class WorkManager:
    def __init__(self, config: WorkManagerConfiguration, *, alert_poller: AlertPoller):
        self.config = config
        self._alert_poller = alert_poller

    async def start(self):
        await self._poll_alerts()

    async def _poll_alerts(self):
        while True:
            logging.info("Polling alerts")  # TODO:

            alerts = await self._alert_poller.poll_alerts(
                self.config.alerts_batch_limit
            )

            print("New alerts", alerts)  # TODO:

            await asyncio.sleep(self.config.alerts_poll_interval)
