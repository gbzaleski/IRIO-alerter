#!/usr/bin/env python3
import os
import sys
import uuid
import multiprocessing
import uvicorn
import structlog
from structlog.contextvars import merge_contextvars
from structlog_gcp import processors


from .settings import Settings, AlertPollerConfiguration, WorkManagerConfiguration


def build_structlog_processors():
    procs = [
        merge_contextvars,
    ]
    procs.extend(processors.CoreCloudLogging().setup())
    procs.extend(processors.LogSeverity().setup())
    procs.extend(processors.CodeLocation().setup())
    procs.extend(processors.FormatAsCloudLogging().setup())

    return procs


structlog.configure(processors=build_structlog_processors())


def get_settings() -> Settings:
    mode = os.environ.get("INSTANCE_MODE")

    alerter_id = os.environ.get("ALERTER_ID")
    if alerter_id is None:
        alerter_id = str(uuid.uuid4())
        os.environ["ALERTER_ID"] = alerter_id

    if mode == "dev":
        settings = Settings(
            alerter_id=alerter_id,
            run_server=False,
            run_worker=True,
            poller_config=AlertPollerConfiguration(
                alerter_id=alerter_id,
                covered_shards=list(range(64)),
                lease_duration=10000,
            ),
            work_manager_config=WorkManagerConfiguration(
                alerter_id=alerter_id,
                alerts_batch_limit=100,
                alerts_poll_interval=10.0,
            ),
        )
    elif mode == "production":
        settings = Settings(
            alerter_id=alerter_id,
            run_server=False,
            run_worker=True,
            use_real_sender=False,
            poller_config=AlertPollerConfiguration(
                alerter_id=alerter_id,
                covered_shards=list(range(64)),
                lease_duration=10000,
            ),
            work_manager_config=WorkManagerConfiguration(
                alerter_id=alerter_id,
                alerts_batch_limit=100,
                alerts_poll_interval=10.0,
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
    if settings.run_server:
        config = uvicorn.Config("api.main:app", port=8000, log_level="info")
        server = uvicorn.Server(config)
        server.run()


if __name__ == "__main__":
    main()
