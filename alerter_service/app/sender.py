import abc
from pydantic import BaseModel

from .types import Alert, AlerterId, AlertId, ContactMethod
from google.cloud import secretmanager

def access_secret_version(secret_id):
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{PROJECT_ID}/secrets/{secret_id}/versions/latest"
    response = client.access_secret_version(name=name)
    return response.payload.data.decode('UTF-8')

MAILJET_API_KEY = access_secret_version("MAILJET_API_KEY")
MAILJET_SECRET_KEY = access_secret_version("MAILJET_SECRET_KEY")

class AlertSenderConfiguration(BaseModel):
    alerter_id: AlerterId


class AlertSender(abc.ABC):
    def __init__(self, config: AlertSenderConfiguration):
        self.config = config

    @abc.abstractmethod
    async def send_alert(self, alert: Alert, contact_method: ContactMethod):
        pass


class AlertStateManager(abc.ABC):
    @abc.abstractmethod
    async def mark_alerts_as_sent(self, alerts: list[Alert]):
        pass

    @abc.abstractmethod
    async def get_contact_methods_for_alerts(
        self, alerts: list[Alert]
    ) -> dict[AlertId, ContactMethod]:
        pass


class AlertSenderManagerConfiguration(BaseModel):
    alerter_id: AlerterId


class AlertSenderManager:
    def __init__(
        self,
        config: AlertSenderManagerConfiguration,
        *,
        alert_sender: AlertSender,
        alert_state_manager: AlertStateManager
    ):
        self.config = config
        self._alert_sender = alert_sender
        self._alert_state_manager = alert_state_manager

    async def send_alerts(self, alerts: list[Alert]):
        contact_methods = (
            await self._alert_state_manager.get_contact_methods_for_alerts(alerts)
        )

        for alert in alerts:
            contact_method = contact_methods.get(alert.alertId)
            if contact_method is not None:
                await self._alert_sender.send_alert(alert, contact_method)
                await self._alert_state_manager.mark_alerts_as_sent([alert])
                # TODO: improve efficiency of processing
                print("Sent alert", alert.alertId)
