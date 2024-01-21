from pydantic import BaseModel
from .common.types import ServiceId, Miliseconds

ServiceId = str
MonitorId = str

Miliseconds = int


class MonitoredServiceInfo(BaseModel):
    serviceId: ServiceId
    url: str
    frequency: Miliseconds
    alertingWindow: Miliseconds
    allowedResponseTime: Miliseconds
