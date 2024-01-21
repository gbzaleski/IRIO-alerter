from datetime import datetime
from pydantic import BaseModel
from .common.types import ServiceId, MonitorId, Miliseconds


class MonitoredServiceInfo(BaseModel):
    serviceId: ServiceId
    url: str
    frequency: Miliseconds
    alertingWindow: Miliseconds
    allowedResponseTime: Miliseconds


class MonitoredServicesLease(BaseModel):
    serviceId: ServiceId
    monitorId: MonitorId
    leasedAt: datetime
    leasedTo: datetime
