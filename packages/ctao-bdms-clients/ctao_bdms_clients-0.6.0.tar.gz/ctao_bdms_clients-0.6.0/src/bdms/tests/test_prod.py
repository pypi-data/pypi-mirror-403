import json
import logging
import os
import secrets
import time
from collections import OrderedDict
from pathlib import Path

import pytest
from rucio.client.client import ReplicaClient
from rucio.common.utils import extract_scope

from bdms.tests.utils import (
    fetch_ingestion_daemon_metrics,
)


def write_chunked(fullpath, size_mb, chunk_size_mb=10):
    """Write a file in chunks to avoid using too much memory at once."""

    with open(fullpath, "wb") as f:
        written = 0
        while written < size_mb:
            n = min(size_mb - written, chunk_size_mb)
            f.write(b"0" * n * 1024 * 1024)
            written += n


def update_replication_status(all_created_files, replica_client):
    replicas = list(
        replica_client.list_replicas(
            [_["did"] for _ in all_created_files.values()],
        )
    )

    logging.info("Checking replication status for %d files", len(all_created_files))

    for r in replicas:
        lfn = r["name"]

        entry = all_created_files[lfn]

        entry["n_replicas"] = len(r["pfns"])
        entry["ingested"] = entry["n_replicas"] > 0
        # replicated means that two long-term copies exist in addition to the original on the ingestion storage
        entry["replicated"] = len(r["pfns"]) > 2

        logging.info(
            "File %s: ingested=%s, replicated=%s, n_replicas=%d ",
            lfn,
            entry["ingested"],
            entry["replicated"],
            entry["n_replicas"],
        )


def create_file(file_info):
    """Create a file and its trigger file based on the provided file information."""

    full_path = file_info["full_path"]
    size_mb = file_info["size_mb"]

    write_chunked(full_path, size_mb)
    os.symlink(full_path, f"{full_path}.trigger")


@pytest.mark.verifies_usecase("UC-110-1.1.4")
@pytest.mark.prod
def test_ingest_parallel_submission_with_live_daemon(request):
    """
    Test parallel file processing with full nominally-operational BDMS.

    This test can be run in a pre-production or production environment. It safely creates files in a test area.

    The test contains mock-up of acada writing files to BDMS monitored area. So it should be run on-site next to the ingestion daemon.
    It should be run as part of BDMS helm test.

    We make sure that the test is operational by running it in BDMS CI with reduce number of files and size.

    This test needs to run in on-site environment with ingestion daemon running and monitoring the test area.
    In principle it does not have access to files being ingested, only to rucio server.
    """

    # an alternative implementation would be to make an agent which imitates acada writing files, and control this service from the test
    # it's a bit more complex, and we still want to have a test with well-defined start and end points, and a report at the end

    config = json.loads(request.config.getoption("--prod-config"))

    interval_between_new_files_seconds = config.get(
        "interval_between_new_files_seconds", 0.5
    )
    file_size_mb = config.get("file_size_mb", 1)
    number_of_files = config.get("number_of_files", 3)
    vo_name = config.get("vo_name", "ctao.dpps.test")
    data_prefix = Path(
        config.get("data_prefix", f"/storage-1/{vo_name}/test_scope_persistent/")
    )
    max_wait_after_end_of_file_creation_seconds = config.get(
        "wait_after_end_of_file_creation_seconds", 10
    )
    wait_after_end_of_file_creation_interval_seconds = config.get(
        "wait_after_end_of_file_creation_interval_seconds", 1
    )

    # make sure we got the vo in the data prefix
    assert vo_name in data_prefix.parts
    # make sure we got at least one directory more than just the vo
    vo_index = data_prefix.parts.index(vo_name)
    assert vo_index < (len(data_prefix.parts) - 1)
    rse_prefix = data_prefix.parents[vo_index]

    replica_client = ReplicaClient()

    files_for_ingestion = OrderedDict()

    series_id = "{}-{}".format(secrets.token_hex(4), time.strftime("%Y%m%d-%H%M%S"))

    dl0 = data_prefix / "DL0"
    date_pattern = time.strftime("%Y/%m/%d")

    subarray_dir = dl0 / "ARRAY" / "ctao-north" / "event" / date_pattern
    tel_event_dir = dl0 / "LSTN-01" / "ctao-north" / "event" / date_pattern
    mon_dir = dl0 / "ARRAY" / "ctao-north" / "monitoring" / date_pattern

    # only tel_event_dir will be used for file creation for now
    for d in [subarray_dir, tel_event_dir, mon_dir]:
        d.mkdir(parents=True, exist_ok=True)

    for number_of_files_created in range(number_of_files):
        fn = f"dummy_file_{series_id}_{number_of_files_created}.fits"

        full_path = tel_event_dir / fn

        relative_to_prefix = full_path.relative_to(rse_prefix).as_posix()
        lfn = f"/{relative_to_prefix}"
        scope, _ = extract_scope(lfn)

        logging.info("Creating file %s", full_path)
        logging.info("LFN: %s", lfn)

        files_for_ingestion[lfn] = {
            "full_path": str(full_path),
            "created": False,
            "short_name": fn,
            "size_mb": file_size_mb,
            "created_at": time.time(),
            "n_replicas": 0,
            "ingested": False,
            "replicated": False,
            "did": {"scope": scope, "name": lfn},
        }

    for fn, file_info in files_for_ingestion.items():
        create_file(file_info)

        metrics = fetch_ingestion_daemon_metrics()

        logging.info(
            "n_tasks_success_created: %s", metrics.get("n_tasks_success_created")
        )
        logging.info(
            "n_tasks_processed_total: %s", metrics.get("n_tasks_processed_total")
        )

        update_replication_status(files_for_ingestion, replica_client)

        time.sleep(interval_between_new_files_seconds)

    # wait for all files to be ingested and replicated
    start_wait_time = time.time()
    while time.time() - start_wait_time < max_wait_after_end_of_file_creation_seconds:
        update_replication_status(files_for_ingestion, replica_client)

        time.sleep(wait_after_end_of_file_creation_interval_seconds)

    # final check that all files are ingested
    problematic_files = {
        fn: info
        for fn, info in files_for_ingestion.items()
        if not info["ingested"] or not info["replicated"]
    }

    for fn, info in problematic_files.items():
        logging.warning(
            "File %s: ingested=%s, replicated=%s, n_replicas=%d ",
            fn,
            info["ingested"],
            info["replicated"],
            info["n_replicas"],
        )

    # unlike normal tests, prod test only fails in rare cases, so we log and collect the result instead of asserting

    # We might also collect relevant statistics from prometheus about CPU/RAM/Disk load, ingestion rate, replication rate, etc.
    # keep references to preserved monitoring data
