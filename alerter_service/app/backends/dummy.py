import logging
from alerter_service.app.types import Alert
from ..types import ContactMethod
from ..sender import AlertSender


class AlertSenderDummy(AlertSender):
    async def send_alert(self, alert: Alert, contact_method: ContactMethod):
        print("Sending alert", alert.alertId, "to", contact_method.email)
