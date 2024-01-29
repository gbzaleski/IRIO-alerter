import structlog

from ..types import ContactMethod, Alert
from ..sender import AlertSender

logger = structlog.stdlib.get_logger()


class AlertSenderDummy(AlertSender):
    async def send_alert(self, alert: Alert, contact_method: ContactMethod) -> bool:
        logger.info(f"Dummy sending alert {alert.alertId}", alertId=alert.alertId)
        return True
