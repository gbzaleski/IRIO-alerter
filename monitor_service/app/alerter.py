import abc
from datetime import datetime
from pydantic import BaseModel
from .types import ServiceId, MonitorId, Miliseconds


class Alert(BaseModel):
    serviceId: ServiceId
    monitorId: MonitorId
    timestamp: datetime


class AlerterConfiguration(BaseModel):
    alert_cooldown: Miliseconds


class Alerter(abc.ABC):
    def __init__(self, config: AlerterConfiguration):
        self.config = config

    @abc.abstractmethod
    async def send_alert(self, alert: Alert):
        pass
