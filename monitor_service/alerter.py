import abc
from enum import Enum
from datetime import datetime
from pydantic import BaseModel
from .types import ServiceId, MonitorId, Miliseconds

class Alert(BaseModel):
    serviceId: ServiceId
    monitorId: MonitorId
    timestamp: datetime

ALERT_COOLDOWN: Miliseconds = 20000

class Alerter(abc.ABC):

    @abc.abstractmethod
    async def send_alert(self, alert: Alert):
        pass
