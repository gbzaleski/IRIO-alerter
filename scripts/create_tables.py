#!/usr/bin/env python

import os
import argparse
import base64
import datetime
import decimal
import json
import logging
import time

from google.cloud import spanner
from google.cloud.spanner_admin_instance_v1.types import spanner_instance_admin
from google.cloud.spanner_v1 import param_types
from google.cloud.spanner_v1 import DirectedReadOptions
from google.type import expr_pb2
from google.iam.v1 import policy_pb2
from google.cloud.spanner_v1.data_types import JsonObject
from google.protobuf import field_mask_pb2  # type: ignore

OPERATION_TIMEOUT_SECONDS = 240

MIGRATIONS_DIR = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "../migrations")
)
PROJECT_ID = os.environ.get("PROJECT_ID", "test-project")
SPANNER_EMULATOR_URL = os.environ.get("SPANNER_EMULATOR_URL", "http://spanner:9020/")
INSTANCE_NAME = os.environ.get("INSTANCE_NAME", "test-instance")
DATABASE_NAME = os.environ.get("DATABASE_NAME", "test-database")


def create_tables():
    spanner_client = spanner.Client(project=PROJECT_ID)
    instance = spanner_client.instance(INSTANCE_NAME)

    with open(os.path.join(MIGRATIONS_DIR, "ddl/schema.sql"), "r") as f:
        ddl_statement = f.read()

    db = instance.database(DATABASE_NAME, ddl_statements=[ddl_statement])

    operation = db.create()

    print("Waiting for operation to complete...")
    operation.result(OPERATION_TIMEOUT_SECONDS)

def insert_data_with_dml():
    """Inserts sample data into the given database using a DML statement."""

    spanner_client = spanner.Client(project=PROJECT_ID)
    instance = spanner_client.instance(INSTANCE_NAME)
    database = instance.database(DATABASE_NAME)

    with open(os.path.join(MIGRATIONS_DIR, "dml/example.sql"), "r") as f:
        s = f.read()

    def insert_monitored_services(transaction):
        row_ct = transaction.execute_update(
            s
        )

        print("{} record(s) inserted.".format(row_ct))

    database.run_in_transaction(insert_monitored_services)

def query_data():
    """Queries sample data from the database using SQL."""
    spanner_client = spanner.Client(project=PROJECT_ID)
    instance = spanner_client.instance(INSTANCE_NAME)
    database = instance.database(DATABASE_NAME)

    with database.snapshot() as snapshot:
        results = snapshot.execute_sql(
            "SELECT ServiceId, Url FROM MonitoredServices"
        )

        for row in results:
            print("ServiceId: {}, Url: {}".format(*row))