import abc
from typing import Annotated
import annotated_types
from pydantic import BaseModel, conset
from .common.types import SHARDS_COUNT, Miliseconds
from .types import AlerterId


class AlertPollerConfiguration(BaseModel):
    alerter_id: AlerterId
    covered_shards: conset(
        Annotated[int, annotated_types.Ge(0), annotated_types.Lt(SHARDS_COUNT)],
        min_length=1,
    )
    lease_duration: Miliseconds


class AlertPoller(abc.ABC):
    def __init__(self, config: AlertPollerConfiguration):
        self.config = config

    @abc.abstractmethod
    async def poll_alerts(self, alerts_limit: int):
        pass
