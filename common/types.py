from enum import Enum

ServiceId = str
AlerterId = str
MonitorId = str

Miliseconds = int

SHARDS_COUNT = 64


class AlertStatus(Enum):
    SUBMITTED = 0
    LEASED1 = 1
    NOTIFY1 = 2
    LEASED2 = 3
    NOTIFY2 = 4
    ACK = 5
