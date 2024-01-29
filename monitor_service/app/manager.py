import asyncio
import signal
from pydantic import BaseModel
import structlog
from structlog.contextvars import bind_contextvars

from .poller import WorkPoller
from .alerter import Alerter
from .monitor import ServiceMonitor, ServiceMonitorConfiguration
from .types import ServiceId, MonitorId, Miliseconds

logger = structlog.stdlib.get_logger()


class WorkManagerConfiguration(BaseModel):
    monitor_id: MonitorId
    max_monitored_services: int = 10  # TODO:
    work_poll_interval: float = 10.0
    monitored_service_timeout: Miliseconds


class WorkManager:
    def __init__(
        self,
        config: WorkManagerConfiguration,
        *,
        work_poller: WorkPoller,
        alerter: Alerter,
    ):
        self.config = config
        self._work_poller = work_poller
        self._alerter = alerter
        self._monitored_services: dict[ServiceId, ServiceMonitor] = {}
        self._background_tasks = set()
        self._monitoring_tasks = {}
        self.running = True
        signal.signal(signal.SIGINT, self._shutdown_gracefully)
        signal.signal(signal.SIGTERM, self._shutdown_gracefully)

    async def start(self):
        # polling_task = asyncio.create_task(self._poll_for_work())
        # self._background_tasks.add(polling_task)
        # polling_task.add_done_callback(self._background_tasks.discard)
        bind_contextvars(monitorId=self.config.monitor_id)
        lease_renew_task = asyncio.create_task(self._renew_lease())
        self._background_tasks.add(lease_renew_task)
        lease_renew_task.add_done_callback(self._background_tasks.discard)
        await self._poll_for_work()

    async def _poll_for_work(self):
        while self.running:
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
            renewed_leases = await self._work_poller.renew_lease(
                list(self._monitored_services.keys())
            )
            logger.info(
                f"Renewed lease on {len(renewed_leases)} services",
                renewed_leases_count=len(renewed_leases),
            )
            for not_renewed in set(self._monitored_services.keys()) - set(
                renewed_leases
            ):
                self._stop_monitoring(not_renewed)
            await asyncio.sleep(lease_renew_interval)

    async def _start_monitoring(self, serviceId: ServiceId):
        logger.info("Start monitoring of service", serviceId=serviceId)
        info_l = await self._work_poller.get_services_info([serviceId])
        if len(info_l) == 0:
            logger.error("Empty service info", serviceId=serviceId)
        else:
            info = info_l[0]
            monitor = ServiceMonitor(
                config=ServiceMonitorConfiguration(
                    monitor_id=self.config.monitor_id,
                    timeout=self.config.monitored_service_timeout,
                ),
                info=info,
                alerter=self._alerter,
            )
            self._monitored_services[serviceId] = monitor
            monitoring_task = asyncio.create_task(monitor.monitor())
            self._monitoring_tasks[serviceId] = monitoring_task
            monitoring_task.add_done_callback(
                lambda _: self._stop_monitoring(serviceId)
            )

    def _stop_monitoring(self, serviceId: ServiceId):
        logger.info("Stop monitoring of service", serviceId=serviceId)
        task = self._monitoring_tasks.pop(serviceId, None)
        if task is not None:
            task.cancel()

        self._monitored_services.pop(serviceId, None)

    def _shutdown_gracefully(self, signum, frame):
        logger.info("Received shutdown signal %d", signum)
        self.running = False
        for task in self._background_tasks:  # FIXME: not safe for threading
            task.cancel()

        for serviceId in list(self._monitored_services.keys()):
            self._stop_monitoring(serviceId)
