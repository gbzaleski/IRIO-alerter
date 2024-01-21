from datetime import datetime
from pydantic import BaseModel
from .common.types import AlerterId, ServiceId, AlertStatus, Miliseconds



class Alert(BaseModel):
    alertId: AlerterId
    serviceId: ServiceId
    detectionTimestamp: datetime
    status: AlertStatus