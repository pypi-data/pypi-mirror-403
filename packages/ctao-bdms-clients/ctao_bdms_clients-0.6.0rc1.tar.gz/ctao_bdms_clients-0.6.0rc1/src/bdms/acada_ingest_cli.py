#!/usr/bin/env python3
"""CLI tool for ACADA Ingestion - Uses IngestionClient and Ingest classes."""

import argparse
import logging
import os
import signal
import sys
import time
from pathlib import Path

from prometheus_client import start_http_server
from ruamel.yaml import YAML

from bdms.acada_ingestion import Ingest, IngestionClient

log = logging.getLogger("acada_cli")


def validate_log_level(value):
    """Validate and convert log level to uppercase."""
    valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
    upper_value = value.upper()
    if upper_value not in valid_levels:
        raise argparse.ArgumentTypeError(
            f"Invalid log level. Choose from: {', '.join(valid_levels)}"
        )
    return upper_value


# validation functions
def offsite_copies_non_negative_int(value):
    """Validate non-negative integer for offsite copies."""
    try:
        int_value = int(value)
        if int_value < 0:
            raise argparse.ArgumentTypeError(
                "Number of offsite copies must be non-negative"
            )
        return int_value
    except ValueError:
        raise argparse.ArgumentTypeError(
            f"Offsite copies must be an integer, got {value!r}"
        )


def validate_metrics_port(value):
    """Validate metrics port range."""
    try:
        int_value = int(value)
        if not (1024 <= int_value <= 65535):
            raise argparse.ArgumentTypeError(
                "Metrics port must be between 1024 and 65535"
            )
        return int_value
    except ValueError:
        raise argparse.ArgumentTypeError(
            f"Metrics port must be an integer, got {value!r}"
        )


def polling_interval_positive_float(value):
    """Validate polling interval."""
    try:
        float_value = float(value)
        if float_value <= 0:
            raise argparse.ArgumentTypeError("Polling interval must be positive")
        return float_value
    except ValueError:
        raise argparse.ArgumentTypeError(
            f"Polling interval must be a number, got {value!r}"
        )


def retry_interval_positive_float(value):
    """Validate retry interval."""
    try:
        float_value = float(value)
        if float_value <= 0:
            raise argparse.ArgumentTypeError("Retry interval must be positive")
        return float_value
    except ValueError:
        raise argparse.ArgumentTypeError(
            f"Retry interval must be a number, got {value!r}"
        )


def validate_data_path(value):
    """Validate data directory path."""
    data_path = Path(value)
    if not data_path.exists():
        raise argparse.ArgumentTypeError(f"Data path does not exist: {value}")
    if not data_path.is_dir():
        raise argparse.ArgumentTypeError(f"Data path is not a directory: {value}")
    return str(data_path)


def _create_parser():
    """Create the main argument parser."""
    parser = argparse.ArgumentParser(
        prog="acada-ingest",
        description="ACADA Ingestion Tool - Process ACADA data products into BDMS using Rucio",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "--config",
        "-c",
        type=argparse.FileType("r"),
        help="Path to configuration file (can be overridden by command line arguments), yaml",
    )

    # Core ingestion
    core_group = parser.add_argument_group("Core Ingestion")
    core_group.add_argument(
        "--data-path",
        "-d",
        type=validate_data_path,
        help="Path to ACADA on-site data directory to monitor for trigger files",
    )

    core_group.add_argument(
        "--offsite-copies",
        type=offsite_copies_non_negative_int,
        default=2,
        help="Number of offsite replica copies to create",
    )

    # Rucio
    rucio_group = parser.add_argument_group("Rucio Configuration")
    rucio_group.add_argument(
        "--rse",
        type=str,
        help="Rucio Storage Element (RSE) name for onsite storage",
    )
    rucio_group.add_argument(
        "--vo", type=str, default="ctao", help="Virtual organization name prefix"
    )

    # Monitoring
    monitoring_group = parser.add_argument_group("Monitoring")
    monitoring_group.add_argument(
        "--metrics-port",
        type=validate_metrics_port,
        default=8000,
        help="Port for Prometheus metrics server",
    )
    monitoring_group.add_argument(
        "--disable-metrics",
        action="store_true",
        help="Disable Prometheus metrics server",
    )

    # Logging
    logging_group = parser.add_argument_group("Logging")
    logging_group.add_argument(
        "--log-level",
        type=validate_log_level,
        default="INFO",
        help="Logging level (case insensitive): DEBUG, INFO, WARNING, ERROR, CRITICAL",
    )
    logging_group.add_argument(
        "--log-file",
        type=str,
        help="Path to log file (if not specified, logs to stdout)",
    )

    # Daemon
    daemon_group = parser.add_argument_group("Daemon Options")
    daemon_group.add_argument(
        "--polling-interval",
        type=polling_interval_positive_float,
        default=1.0,
        help="Interval in seconds for the polling observer to check for new trigger files",
    )

    daemon_group.add_argument(
        "--client-retry-interval",
        type=retry_interval_positive_float,
        default=30.0,
        help="Retry interval in seconds when Ingestion client initialization fails",
    )

    daemon_group.add_argument(
        "--lock-file",
        type=str,
        help="Path to daemon lock file, prevents multiple instances",
    )
    daemon_group.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate configuration without starting daemon",
    )

    return parser


def setup_logging(log_level, log_file=None):
    """Configure structured logging for the daemon."""
    # Validate and sanitize log file path
    if log_file:
        log_path = Path(log_file).resolve()  # Resolve to absolute path

        # Block ".." in file paths for security
        if any(part == ".." for part in log_path.parts):
            raise ValueError("Log file path contains directory traversal")

        # Prevent writing to system-critical directories
        forbidden_dirs = {"/etc", "/boot", "/sys", "/proc", "/dev"}
        if any(str(log_path).startswith(forbidden) for forbidden in forbidden_dirs):
            raise ValueError("Log file path not allowed in system directories")

        # Ensure we can write safely
        try:
            log_path.parent.mkdir(parents=True, exist_ok=True)
            if log_path.exists() and not os.access(log_path, os.W_OK):
                raise PermissionError(f"Cannot write to log file: {log_file}")
        except OSError as e:
            raise ValueError(f"Cannot use log file '{log_file}': {e}") from e

    log_format = (
        "%(asctime)s - %(name)s - %(levelname)s - [PID:%(process)d] - %(message)s"
    )

    # Use validated log level
    log_level_obj = getattr(logging, log_level)

    logging.basicConfig(level=log_level_obj, format=log_format, filename=log_file)

    # Set specific log levels for different components
    logging.getLogger("bdms.acada_ingestion").setLevel(log_level_obj)
    logging.getLogger("acada_cli").setLevel(log_level_obj)

    if log_level == "DEBUG":
        # In debug mode, show more Rucio details
        logging.getLogger("rucio").setLevel(logging.INFO)
    else:
        # Normal operation
        logging.getLogger("rucio").setLevel(logging.WARNING)

    # Reduce noise from external libraries
    external_loggers = [
        "urllib3",
        "requests",
        "watchdog",
        "charset_normalizer",
        "filelock",
    ]
    for logger in external_loggers:
        logging.getLogger(logger).setLevel(logging.WARNING)


def create_ingestion_client(args) -> IngestionClient:
    """Create and validate IngestionClient with provided arguments."""
    while True:
        try:
            client = IngestionClient(
                data_path=args.data_path,
                rse=args.rse,
                vo=args.vo,
                logger=log.getChild("IngestionClient"),
            )
            log.info(
                "Successfully created IngestionClient for RSE '%s'",
                args.rse,
            )
            return client
        except Exception:
            log.exception(
                "Failed to create IngestionClient. Retrying in %.0fs",
                args.client_retry_interval,
            )
            time.sleep(args.client_retry_interval)


def create_ingest_daemon(client: IngestionClient, args) -> Ingest:
    """Create Ingest daemon with provided arguments."""
    try:
        daemon = Ingest(
            client=client,
            top_dir=args.data_path,
            lock_file_path=args.lock_file,
            polling_interval=args.polling_interval,
            offsite_copies=args.offsite_copies,
        )
        log.info(
            "Successfully created Ingest daemon for directory '%s'", args.data_path
        )
        return daemon
    except Exception:
        log.exception("Failed to create Ingest daemon")
        raise


# parser defined as a module level variable
parser = _create_parser()


def parse_args_and_config(args: list) -> argparse.Namespace:
    """Parse command line arguments and configuration file. Config file acts as defaults for CLI."""
    parsed_args = parser.parse_args(args)

    if parsed_args.config:
        yaml = YAML(typ="safe")
        try:
            config_dict = yaml.load(parsed_args.config)
        finally:
            print(f"Closing file: {parsed_args.config}")
            parsed_args.config.close()

        parser.set_defaults(**config_dict)

    parsed_args = parser.parse_args(args)
    if parsed_args.config is not None:
        parsed_args.config.close()
    return parsed_args


def main(args=None, stop_event=None):
    """Run the main CLI entry point."""
    args = parse_args_and_config(args)

    try:
        # Setup logging with error handling
        try:
            setup_logging(args.log_level, args.log_file)
        except ValueError as e:
            print(f"Logging configuration error: {e}", file=sys.stderr)
            raise

        log.info("Starting ACADA ingestion daemon with file system monitoring")
        log.info("Configuration: data_path=%s, rse=%s", args.data_path, args.rse)
        log.info("Monitoring: polling_interval=%ss", args.polling_interval)
        log.info("Replication: offsite_copies=%d", args.offsite_copies)
        log.info("Process ID: %d", os.getpid())

        if args.dry_run:
            log.warning(
                "Dry Run - Validating configuration only, daemon will not start"
            )

        # Normal execution: Start metrics server (if enabled)
        if not args.disable_metrics:
            start_http_server(args.metrics_port)
            log.info("Metrics server started on port %d", args.metrics_port)

        # Create IngestionClient
        client = create_ingestion_client(args)

        # Create and run Ingest daemon
        daemon = create_ingest_daemon(client, args)

        if args.dry_run:
            sys.exit(0)

        main_pid = os.getpid()

        def signal_handler(signum, frame):
            # Handle SIGTERM by shutting down the daemon
            # Normally, receiving sigterm prevents finalizers from being run
            # but we need to shutdown orderly

            # ignore signal in worker processes of multiprocessing pool
            # would otherwise call daemon.shutdown in each worker process.
            if os.getpid() != main_pid:
                return

            if not daemon.stop_event.is_set():
                log.warning("Received signal %d, shutting down.", signum)
                daemon.stop_event.set()
            else:
                log.warning("Shutdown already in progress.")

        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)
        log.info("Registered signal handler for SIGTERM/SIGINT")

        log.info("Starting ACADA ingestion daemon with file system monitoring...")
        log.info(
            "The daemon will monitor for .trigger files and process corresponding data files"
        )
        log.info("Use Ctrl+C to stop the daemon gracefully")

        if stop_event:
            daemon.stop_event = stop_event

        # Run the daemon (this blocks until shutdown)
        daemon.run()
    except Exception:
        log.exception("Fatal error occurred")
        sys.exit(1)


if __name__ == "__main__":
    main()
