import abc
from pydantic import BaseModel, PositiveInt
from .types import ServiceId, MonitorId, Miliseconds, MonitoredServiceInfo


class WorkPollerConfiguration(BaseModel):
    monitor_id: MonitorId
    lease_duration: Miliseconds
    monitor_replication_factor: PositiveInt


class WorkPoller(abc.ABC):
    def __init__(self, config: WorkPollerConfiguration):
        self.config = config

    @abc.abstractmethod
    async def poll_for_work(
        self,
        new_services_limit: int,
        already_monitored_services: list[ServiceId],
    ) -> list[ServiceId]:
        pass

    @abc.abstractmethod
    async def renew_lease(
        self,
        services: list[ServiceId],
    ) -> None:
        pass

    @abc.abstractmethod
    async def get_services_info(
        self, services: list[ServiceId]
    ) -> list[MonitoredServiceInfo]:
        pass
