from typing import Optional
import asyncio
import httpx
from httpx import TimeoutException, RequestError
from pydantic import BaseModel
import structlog

from .types import MonitorId, MonitoredServiceInfo, Miliseconds
from .alerter import Alert, Alerter
from .utils import get_time, time_difference_in_ms

logger = structlog.stdlib.get_logger()


class ServiceMonitorConfiguration(BaseModel):
    monitor_id: MonitorId
    timeout: Miliseconds


class ServiceMonitor:
    config: ServiceMonitorConfiguration
    info: MonitoredServiceInfo
    _alerter: Alerter
    last_response_time: Optional[float]

    def __init__(
        self,
        config: ServiceMonitorConfiguration,
        info: MonitoredServiceInfo,
        *,
        alerter: Alerter,
    ):
        self.config = config
        self.info = info
        self.last_response_time = None
        self._alerter = alerter

    async def monitor(self):
        self.last_response_time = get_time()  # fake first response time

        sleep_time = self.info.frequency / 1000

        while True:
            await asyncio.gather(
                self._check_service_heartbeat(), asyncio.sleep(sleep_time)
            )

    async def _check_service_heartbeat(self):
        """

        Should finish in time < monitoring frequency #TODO: add metric
        """
        timeout_s = min(self.info.frequency / 2000, self.config.timeout / 1000)
        url = str(self.info.url)
        async with httpx.AsyncClient() as client:
            errored = False
            try:
                r = await client.get(url, timeout=timeout_s)
                self.last_response_time = get_time()
                if r.status_code != 200:
                    logger.warning(
                        f"Service {self.info.serviceId} responded with status code {r.status_code}",
                        serviceId=self.info.serviceId,
                        status_code=r.status_code,
                    )
                    errored = True
            except RequestError as e:
                logger.warning(
                    f"Service {self.info.serviceId} did not respond correctly within allowed time",
                    serviceId=self.info.serviceId,
                    exception_type=type(e).__name__,
                )
                errored = True

            if errored:
                should_send = self._should_send_alert()
                if should_send:
                    await self._send_alert()

    def _should_send_alert(self) -> bool:
        current_time = get_time()
        time_since_last_response = time_difference_in_ms(
            self.last_response_time, current_time
        )
        return time_since_last_response > self.info.alertingWindow

    async def _send_alert(self):
        serviceId = self.info.serviceId
        logger.info("Sending alert", serviceId=serviceId)

        await self._alerter.send_alert(
            Alert(
                serviceId=serviceId,
                monitorId=self.config.monitor_id,
                timestamp=get_time(),  # TODO:
            )
        )
