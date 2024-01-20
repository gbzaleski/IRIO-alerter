from pydantic import BaseModel


ServiceId = str
MonitorId = str

Miliseconds = int


class MonitoredServiceInfo(BaseModel):
    serviceId: ServiceId
    url: str
    frequency: Miliseconds
    alertingWindow: Miliseconds
    allowedResponseTime: Miliseconds
