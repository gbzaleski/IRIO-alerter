import os
from pydantic import BaseModel

from fastapi import FastAPI

app = FastAPI()


class MonitorBasicInfo(BaseModel):
    monitor_id: str
    # started_at: datetime


@app.get("/")
async def read_root():
    return MonitorBasicInfo(monitor_id=os.environ.get("MONITOR_ID"))
