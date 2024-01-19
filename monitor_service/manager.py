import asyncio
from pydantic import BaseModel
from .types import ServiceId, Miliseconds


class WorkManagerConfig(BaseModel):
    max_monitored_services: int = 10  # TODO:
    work_poll_interval: float = 10.0


class WorkManager:
    def __init__(self, config: WorkManagerConfig, *, work_poller: "WorkPoller"):
        self.work_poller = work_poller

        self.config = config
        self.monitored_services = {}

    async def poll_for_work(self):
        # TODO:
        new_services_limit = self.config.max_monitored_services - len(
            self.monitored_services
        )
        if new_services_limit > 0:
            new_services = await self.work_poller.poll_for_work(
                new_services_limit, self.monitored_services
            )
            # TODO:
        await asyncio.sleep(self.config.work_poll_interval)


class WorkPoller:
    async def poll_for_work(self, new_services_limit: int, already_monitored_services):
        pass

    async def renew_lease(self, services: list[ServiceId], lease_time_ms: Miliseconds):
        pass
