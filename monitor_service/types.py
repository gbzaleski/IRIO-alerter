from pydantic import BaseModel, HttpUrl
from .common.types import ServiceId, Miliseconds

ServiceId = str
MonitorId = str

Miliseconds = int


class MonitoredServiceInfo(BaseModel):
    serviceId: ServiceId
    url: HttpUrl
    frequency: Miliseconds
    alertingWindow: Miliseconds
    allowedResponseTime: Miliseconds
