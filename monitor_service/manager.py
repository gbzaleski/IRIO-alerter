import asyncio
from pydantic import BaseModel
from .poller import WorkPoller
from .alerter import Alerter
from .monitor import ServiceMonitor, ServiceMonitorConfiguration
from .types import ServiceId, MonitorId


class WorkManagerConfiguration(BaseModel):
    monitor_id: MonitorId
    max_monitored_services: int = 10  # TODO:
    work_poll_interval: float = 10.0


class WorkManager:
    def __init__(self, config: WorkManagerConfiguration, *, work_poller: WorkPoller, alerter: Alerter):
        self.config = config
        self._work_poller = work_poller
        self._alerter = alerter
        self._monitored_services: dict[ServiceId, ServiceMonitor] = {}
        self._background_tasks = set()

    async def start(self):
        # polling_task = asyncio.create_task(self._poll_for_work())
        # self._background_tasks.add(polling_task)
        # polling_task.add_done_callback(self._background_tasks.discard)
        await self._poll_for_work()
        

    async def _poll_for_work(self):
        # TODO:
        while True:
            print("Polling for work") #TODO: log
            new_services_limit = self.config.max_monitored_services - len(
                self._monitored_services
            )
            if new_services_limit > 0:
                new_services = await self._work_poller.poll_for_work(
                    new_services_limit, self._monitored_services
                )
                print("New services", new_services) #TODO: log
                for service in new_services:
                    await self._start_monitoring(service)
                # TODO:
            await asyncio.sleep(self.config.work_poll_interval)

    async def _start_monitoring(self, service_id: ServiceId):
        print("Start monitoring", service_id) #TODO: log
        info_l = await self._work_poller.get_services_info([service_id])
        if len(info_l) == 0:
            print("Error: empty service info") #TODO: log
        else:
            info = info_l[0]
            monitor = ServiceMonitor(config=ServiceMonitorConfiguration(monitor_id=self.config.monitor_id), info=info, alerter=self._alerter)
            monitoring_task = asyncio.create_task(monitor.monitor())
            self._background_tasks.add(monitoring_task)
            monitoring_task.add_done_callback(self._background_tasks.discard)



