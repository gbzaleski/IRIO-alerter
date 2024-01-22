from datetime import datetime
from pydantic import BaseModel, EmailStr, HttpUrl
from .common.types import ServiceId, MonitorId, AlerterId, Miliseconds, AlertStatus


class MonitoredServiceInfo(BaseModel):
    serviceId: ServiceId
    url: HttpUrl
    frequency: Miliseconds
    alertingWindow: Miliseconds
    allowedResponseTime: Miliseconds


class MonitoredServiceInsertRequest(BaseModel):
    url: HttpUrl
    frequency: Miliseconds
    alertingWindow: Miliseconds
    allowedResponseTime: Miliseconds


class MonitoredServiceInsertResponse(BaseModel):
    serviceId: ServiceId


class MonitoredServicesLease(BaseModel):
    serviceId: ServiceId
    monitorId: MonitorId
    leasedAt: datetime
    leasedTo: datetime


class Alert(BaseModel):
    alertId: AlerterId
    serviceId: ServiceId
    detectionTimestamp: datetime
    status: AlertStatus


class ContactMethod(BaseModel):
    email: EmailStr
