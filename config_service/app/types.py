from datetime import datetime
from typing import Annotated
import annotated_types
from pydantic import BaseModel, EmailStr, HttpUrl, conlist
from .common.types import ServiceId, MonitorId, AlerterId, Miliseconds, AlertStatus


class MonitoredServiceInfo(BaseModel):
    serviceId: ServiceId
    url: HttpUrl
    frequency: Miliseconds
    alertingWindow: Miliseconds
    allowedResponseTime: Miliseconds


class ContactMethod(BaseModel):
    email: EmailStr


class MonitoredServiceInsertRequest(BaseModel):
    url: HttpUrl
    frequency: Annotated[Miliseconds, annotated_types.Ge(1000)]
    alertingWindow: Annotated[Miliseconds, annotated_types.Ge(1000)]
    allowedResponseTime: Annotated[Miliseconds, annotated_types.Ge(30000)]
    contact_methods: conlist(ContactMethod, min_length=2, max_length=2)


class MonitoredServiceUpdateRequest(BaseModel):
    url: HttpUrl
    frequency: Annotated[Miliseconds, annotated_types.Ge(1000)]
    alertingWindow: Annotated[Miliseconds, annotated_types.Ge(1000)]
    allowedResponseTime: Annotated[Miliseconds, annotated_types.Ge(30000)]
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


class ActiveMonitor(BaseModel):
    monitorId: MonitorId
    leasedTo: datetime
