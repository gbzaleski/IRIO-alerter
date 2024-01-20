import abc
from enum import Enum
from datetime import datetime
from pydantic import BaseModel
from .types import ServiceId, MonitorId, Miliseconds

class Alert(BaseModel):
    serviceId: ServiceId
    monitorId: MonitorId
    timestamp: datetime

class AlertStatus(Enum):
    SUBMITTED = 0
    NOTIFY1 = 1
    NOTIFY2 = 2
    ACK = 3

ALERT_COOLDOWN: Miliseconds = 20000

class Alerter(abc.ABC):

    @abc.abstractmethod
    async def send_alert(self, alert: Alert):
        pass
