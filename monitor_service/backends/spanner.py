from google.cloud import spanner
from google.cloud.spanner_v1.instance import Instance
from google.cloud.spanner_v1.database import Database
from ..alerter import Alert


class AlerterSpanner:
    _spanner_client: spanner.Client
    _instance: Instance
    _database: Database

    def __init__(self, spanner_client: spanner.Client):
        self._spanner_client = spanner_client
        self._instance = spanner_client.instance()  # TODO:
        self._database = self._instance.database()  # TODO:

    async def send_alert(self, alert: Alert):
        pass  # TODO:

    async def _get_timestamp(self):
        with self._database.snapshot() as snapshot:
            results = snapshot.execute_sql("SELECT CURRENT_TIMESTAMP() AS now")
            # TODO:


class WorkPollerSpanner:
    async def poll_for_work(self, new_services_limit: int, already_monitored_services):
        pass  # TODO:
