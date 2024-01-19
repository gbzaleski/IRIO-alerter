from pydantic import BaseModel


class Alert(BaseModel):
    serviceId: int
    monitorId: int
    # timestamp - currently not used


class Alerter:
    async def send_alert(self, alert: Alert):
        pass
