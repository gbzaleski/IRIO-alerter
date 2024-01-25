import asyncio
from pydantic import BaseModel
import structlog

from .poller import WorkPoller
from .alerter import Alerter
from .monitor import ServiceMonitor, ServiceMonitorConfiguration
from .types import ServiceId, MonitorId

logger = structlog.stdlib.get_logger()


class WorkManagerConfiguration(BaseModel):
    monitor_id: MonitorId
    max_monitored_services: int = 10  # TODO:
    work_poll_interval: float = 10.0


class WorkManager:
    def __init__(
        self,
        config: WorkManagerConfiguration,
        *,
        work_poller: WorkPoller,
        alerter: Alerter
    ):
        self.config = config
        self._work_poller = work_poller
        self._alerter = alerter
        self._monitored_services: dict[ServiceId, ServiceMonitor] = {}
        self._background_tasks = set()

    async def start(self):
        # polling_task = asyncio.create_task(self._poll_for_work())
        # self._background_tasks.add(polling_task)
        # polling_task.add_done_callback(self._background_tasks.discard)
        lease_renew_task = asyncio.create_task(self._renew_lease())
        self._background_tasks.add(lease_renew_task)
        lease_renew_task.add_done_callback(self._background_tasks.discard)
        await self._poll_for_work()

    async def _poll_for_work(self):
        while True:
            logger.info("Polling for work")
            new_services_limit = self.config.max_monitored_services - len(
                self._monitored_services
            )
            if new_services_limit > 0:
                new_services = await self._work_poller.poll_for_work(
                    new_services_limit, self._monitored_services
                )
                for service in new_services:
                    await self._start_monitoring(service)
            await asyncio.sleep(self.config.work_poll_interval)

    async def _renew_lease(self):
        lease_renew_interval = self._work_poller.config.lease_duration / 3000
        while True:
            logger.info("Renewing lease on monitored services")
            await self._work_poller.renew_lease(list(self._monitored_services.keys()))
            await asyncio.sleep(lease_renew_interval)

    async def _start_monitoring(self, serviceId: ServiceId):
        logger.info("Start monitoring of service", serviceId=serviceId)
        info_l = await self._work_poller.get_services_info([serviceId])
        if len(info_l) == 0:
            logger.error("Empty service info", serviceId=serviceId)
        else:
            info = info_l[0]
            monitor = ServiceMonitor(
                config=ServiceMonitorConfiguration(monitor_id=self.config.monitor_id),
                info=info,
                alerter=self._alerter,
            )
            self._monitored_services[serviceId] = monitor
            monitoring_task = asyncio.create_task(monitor.monitor())
            self._background_tasks.add(monitoring_task)
            monitoring_task.add_done_callback(self._background_tasks.discard)
