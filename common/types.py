from enum import Enum
from pydantic import PositiveInt

ServiceId = str
AlertId = str
AlerterId = str
MonitorId = str

Miliseconds = PositiveInt

SHARDS_COUNT = 64


class AlertStatus(Enum):
    SUBMITTED = 0
    NOTIFY1 = 1
    NOTIFY2 = 2
    ACK = 200
