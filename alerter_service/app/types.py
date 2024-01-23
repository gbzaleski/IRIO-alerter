from datetime import datetime
from pydantic import BaseModel
from .common.types import AlerterId, ServiceId, AlertId, AlertStatus, Miliseconds


class Alert(BaseModel):
    alertId: AlerterId
    serviceId: ServiceId
    detectionTimestamp: datetime
    status: AlertStatus


class ContactMethod(BaseModel):
    email: str
