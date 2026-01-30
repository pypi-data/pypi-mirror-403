"""Celery tasks for ACADA file ingestion into BDMS.

This module defines Celery tasks for asynchronously ingesting ACADA data files
into Rucio, including replica registration and replication rule creation.
"""

import os

from celery import Celery
from rucio.common.exception import (
    CannotAuthenticate,
    ServerConnectionException,
    ServiceUnavailable,
)

app = Celery("acada_ingestion")
app.conf.task_serializer = "json"
app.conf.result_serializer = "json"
app.conf.accept_content = ["json"]


def bool_or_float(string):
    """Parse a string that can either be a float or a boolean."""
    try:
        return float(string)
    except ValueError:
        return string.lower() == "true"


TASK_MAX_RETRIES = int(os.getenv("CELERY_TASK_MAX_RETRIES", 10))
TASK_RETRY_BACKOFF = bool_or_float(os.getenv("CELERY_TASK_RETRY_BACKOFF", "true"))
TASK_RETRY_BACKOFF_MAX = float(os.getenv("CELERY_TASK_RETRY_BACKOFF_MAX", "600.0"))
TASK_RETRY_JITTER = os.getenv("CELERY_TASK_RETRY_JITTER", "true").lower() == "true"

AUTORETRY_EXCEPTIONS = (
    ConnectionError,
    TimeoutError,
    OSError,
    RuntimeError,
    ServerConnectionException,
    CannotAuthenticate,
    ServiceUnavailable,
)


@app.task(
    max_retries=TASK_MAX_RETRIES,
    retry_backoff=TASK_RETRY_BACKOFF,
    retry_backoff_max=TASK_RETRY_BACKOFF_MAX,
    retry_jitter=TASK_RETRY_JITTER,
    autoretry_for=AUTORETRY_EXCEPTIONS,
)
def process_acada_file(
    file_path: str,
    data_path: str,
    rse: str,
    vo: str = "ctao",
    copies: int = 2,
):
    """Celery task to ingest an ACADA file into Rucio for BDMS ingestion.

    Registers the file as a replica on the onsite RSE and creates replication
    rules for offsite copies, and also clean up the trigger file.

    Parameters
    ----------
    file_path : str
        The path to the file to process.
    data_path : str
        Path to data directory.
    rse : str
        Rucio Storage Element (RSE) name.
    vo : str, optional
        Virtual organization name prefix. Defaults to "ctao".
    copies : int, optional
        The number of offsite replicas to create. Defaults to 2.

    Returns
    -------
    dict
        'lfn': Logical File Name
        'file_size': File size in bytes
        'skip_reason': None or name of SkipReason enum
    """
    from bdms.acada_ingestion import IngestionClient, process_file

    client = IngestionClient(data_path=data_path, rse=rse, vo=vo)
    result = process_file(client, file_path, copies=copies)

    # Convert NamedTuple to dict for result and make skip_reason enum to string for JSON serialization
    result_dict = result._asdict()
    if result_dict["skip_reason"] is not None:
        result_dict["skip_reason"] = result_dict["skip_reason"].name

    return result_dict
