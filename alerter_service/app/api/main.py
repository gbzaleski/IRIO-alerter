import os
from typing import Union
from pydantic import BaseModel
from fastapi import FastAPI

app = FastAPI()


class AlerterBasicInfo(BaseModel):
    alerter_id: str
    # started_at: datetime


@app.get("/", response_model=AlerterBasicInfo)
async def read_root():
    return AlerterBasicInfo(alerter_id=os.environ.get("ALERTER_ID"))
