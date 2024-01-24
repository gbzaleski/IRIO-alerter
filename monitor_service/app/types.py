from pydantic import BaseModel, HttpUrl
from .common.types import ServiceId, MonitorId, Miliseconds


class MonitoredServiceInfo(BaseModel):
    serviceId: ServiceId
    url: HttpUrl
    frequency: Miliseconds
    alertingWindow: Miliseconds
    allowedResponseTime: Miliseconds
