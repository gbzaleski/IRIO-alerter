#!/usr/bin/env python3
import os
import sys
import uuid
import multiprocessing
import uvicorn
import structlog
import structlog_gcp
from structlog_gcp import processors

from .settings import (
    Settings,
    AlerterConfiguration,
    WorkPollerConfiguration,
    WorkManagerConfiguration,
)


def build_structlog_processors():
    procs = []

    procs.extend(processors.CoreCloudLogging().setup())
    procs.extend(processors.LogSeverity().setup())
    procs.extend(processors.CodeLocation().setup())
    procs.extend(processors.FormatAsCloudLogging().setup())

    return procs


structlog.configure(processors=structlog_gcp.build_processors())


def get_settings() -> Settings:
    mode = os.environ.get("INSTANCE_MODE")

    monitor_id = os.environ.get("MONITOR_ID")
    if monitor_id is None:
        monitor_id = str(uuid.uuid4())
        os.environ["MONITOR_ID"] = monitor_id

    if mode == "dev":
        settings = Settings(
            monitor_id=monitor_id,
            run_server=False,
            run_worker=True,
            poller_config=WorkPollerConfiguration(
                monitor_id=monitor_id,
                lease_duration=90000,
                monitor_replication_factor=3,
            ),
            work_manager_config=WorkManagerConfiguration(
                monitor_id=monitor_id,
                max_monitored_services=100,
                work_poll_interval=20,
            ),
            alerter_config=AlerterConfiguration(
                alert_cooldown=120000,
            ),
        )
    elif mode == "production":
        settings = Settings(
            monitor_id=monitor_id,
            run_server=False,
            run_worker=True,
            poller_config=WorkPollerConfiguration(
                monitor_id=monitor_id,
                lease_duration=90000,
                monitor_replication_factor=3,
            ),
            work_manager_config=WorkManagerConfiguration(
                monitor_id=monitor_id,
                max_monitored_services=100,
                work_poll_interval=60,
            ),
            alerter_config=AlerterConfiguration(
                alert_cooldown=120000,
            ),
        )
    else:
        raise RuntimeError("INSTANCE_MODE variable not set")

    return settings


def run_worker(settings: Settings):
    from . import worker

    worker.main(settings)


def main():
    abspath = os.path.abspath(__file__)
    dname = os.path.dirname(abspath)
    os.chdir(dname)
    settings = get_settings()
    sys.path.append(dname)

    if settings.run_worker:
        p = multiprocessing.Process(target=run_worker, args=(settings,))
        p.start()
    else:
        p = None
    if settings.run_server:
        config = uvicorn.Config("api.main:app", port=8000, log_level="info")
        server = uvicorn.Server(config)
        server.run()
    if p is not None:
        p.join()


if __name__ == "__main__":
    main()
