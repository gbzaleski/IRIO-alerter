import asyncio
from typing import Optional
from pydantic import BaseModel
import httpx
from httpx import TimeoutException
from .alerter import Alerter
from .utils import get_time, time_difference_in_ms

Miliseconds = int


class MonitoredServiceInfo(BaseModel):
    serviceId: int
    url: str
    frequency: Miliseconds
    alertingWindow: Miliseconds
    allowedResponseTime: Miliseconds


async def monitor_service(service_info: MonitoredServiceInfo):
    entry = ServiceMonitor(service_info, alerter=Alerter())

    await entry.monitor()


class ServiceMonitor:
    info: MonitoredServiceInfo
    alerter: Alerter
    last_response_time: Optional[float]

    def __init__(self, info: MonitoredServiceInfo, *, alerter: Alerter):
        self.info = info
        self.alerter = alerter
        self.last_response_time = None

    async def monitor(self):
        self.last_response_time = get_time()  # fake first response time

        sleep_time = self.info.frequency

        while True:
            await asyncio.gather(
                self._check_service_heartbeat(), asyncio.sleep(sleep_time)
            )

    async def _check_service_heartbeat(self):
        """

        Should finish in time < monitoring frequency #TODO: add metric
        """
        timeout = self.info.frequency / 2000  # TODO: set sensible timeout
        async with httpx.AsyncClient() as client:
            try:
                r = await client.get(self.info.url, timeout=timeout)
                self.last_response_time = get_time()
            except TimeoutException:
                should_send = self._should_send_alert()
                if should_send:
                    await self._send_alert()

    def _should_send_alert(self) -> bool:
        current_time = get_time()
        time_since_last_response = time_difference_in_ms(
            self.last_response_time, current_time
        )
        return time_since_last_response > self.info.alertingWindow
    
    async def _send_alert(self):
        await self.alerter.send_alert() #TODO: logic & should work immediately?


async def f():
    await asyncio.sleep(100)
    print("f")


async def test():
    for x in range(100):
        await asyncio.gather(asyncio.sleep(5), f())
        print(x)


def main():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(test())


if __name__ == "__main__":
    main()
