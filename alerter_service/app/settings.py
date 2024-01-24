from typing import Optional
from pydantic import BaseModel
from .poller import AlertPollerConfiguration
from .manager import WorkManagerConfiguration
from .types import AlerterId


class Settings(BaseModel):
    alerter_id: AlerterId
    run_server: bool = False
    run_worker: bool = False
    use_real_sender: bool = False
    poller_config: AlertPollerConfiguration
    work_manager_config: WorkManagerConfiguration
