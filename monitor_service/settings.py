from pydantic import BaseModel
from .types import MonitorId
from .poller import WorkPollerConfiguration
from .manager import WorkManagerConfiguration
from .alerter import AlerterConfiguration


class Settings(BaseModel):
    monitor_id: MonitorId
    run_server: bool
    run_worker: bool
    poller_config: WorkPollerConfiguration
    work_manager_config: WorkManagerConfiguration
    alerter_config: AlerterConfiguration
