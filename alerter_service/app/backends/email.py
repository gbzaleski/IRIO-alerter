from collections import namedtuple
import os
import structlog
import httpx
from google.cloud import secretmanager

from ..types import ContactMethod, Alert
from ..sender import AlertSender

logger = structlog.stdlib.get_logger()


def access_secret_version(secret_id):
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{PROJECT_ID}/secrets/{secret_id}/versions/latest"
    response = client.access_secret_version(name=name)
    return response.payload.data.decode("UTF-8")


PROJECT_ID = os.environ.get("PROJECT_ID", "test-project")
EXTERNAL_IP = os.environ.get("EXTERNAL_IP")
MAILJET_API_KEY = access_secret_version("MAILJET_API_KEY")
MAILJET_SECRET_KEY = access_secret_version("MAILJET_SECRET_KEY")
SENDER_EMAIL = os.environ.get("SENDER_EMAIL")


class AlertSenderEmail(AlertSender):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._mailer = MailJetSender(
            sender_email=SENDER_EMAIL,
            sender_name="Alerter platform",
            api_key=MAILJET_API_KEY,
            secret_key=MAILJET_SECRET_KEY,
        )

    async def send_alert(self, alert: Alert, contact_method: ContactMethod):
        try:
            date_formatted = alert.detectionTimestamp.strftime("%d/%m/%Y, %H:%M")
            await self._mailer.send_mail(
                (contact_method.email, contact_method.email),
                f"Alert for {alert.serviceId} at {date_formatted}",
                f"Detected downtime of service {alert.serviceId} at {date_formatted}\n Please view the status at http://{EXTERNAL_IP}:8000/docs/\n AlertId: {alert.alertId}",
            )
            return True
        except httpx.HTTPStatusError:
            logger.exception(
                "Error while sending email with alert info for alert %s",
                alert.alertId,
                alertId=alert.alertId,
            )
            return False


Recipient = namedtuple("Recipient", ["recipient_email", "recipient_name"])


class MailJetSender:
    def __init__(
        self, *, sender_email: str, sender_name: str, api_key: str, secret_key: str
    ):
        self.sender_email = sender_email
        self.sender_name = sender_name
        self._api_key = api_key
        self._secret_key = secret_key
        self._client = httpx.AsyncClient()

    async def send_mail(self, recipient: Recipient, title: str, data: str):
        """Funkcja rzuci wyjątek, jeśli otrzymamy kod odpowiedzi inny niż 2xx"""
        (recipient_email, recipient_name) = recipient

        headers = {"Content-Type": "application/json"}
        data = {
            "Messages": [
                {
                    "From": {"Email": self.sender_email, "Name": self.sender_name},
                    "To": [{"Email": recipient_email, "Name": recipient_name}],
                    "Subject": title,
                    "TextPart": data,
                }
            ]
        }
        r = await self._client.post(
            "https://api.mailjet.com/v3.1/send",
            json=data,
            headers=headers,
            auth=(self._api_key, self._secret_key),
        )
        r.raise_for_status()
