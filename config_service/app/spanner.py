import os
from google.cloud import spanner

SPANNER_DATABASE = None


def get_spanner_database():
    global SPANNER_DATABASE
    if SPANNER_DATABASE is not None:
        return SPANNER_DATABASE
    PROJECT_ID = os.environ.get("PROJECT_ID", "test-project")
    INSTANCE_NAME = os.environ.get("INSTANCE_NAME", "test-instance")
    DATABASE_NAME = os.environ.get("DATABASE_NAME", "test-database")

    client = spanner.Client(PROJECT_ID)
    instance = client.instance(INSTANCE_NAME)
    db = instance.database(DATABASE_NAME)
    SPANNER_DATABASE = db
    return db
