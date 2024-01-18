from google.cloud import spanner
from pydantic import BaseModel

class Alert(BaseModel):
    serviceId: int
    monitorId: int
    #timestamp - currently not used

class Alerter:
    
    async def send_alert(self, alert: Alert):
        pass


class AlerterSpanner:
    def __init__(self, spanner_client: spanner.Client):
        self.spanner_client = spanner_client

    async def send_alert(self, alert: Alert):
        pass #TODO: