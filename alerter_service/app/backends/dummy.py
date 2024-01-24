import logging
from ..types import ContactMethod, Alert
from ..sender import AlertSender


class AlertSenderDummy(AlertSender):
    async def send_alert(self, alert: Alert, contact_method: ContactMethod) -> bool:
        print("Sending alert", alert.alertId, "to", contact_method.email)
        return True
