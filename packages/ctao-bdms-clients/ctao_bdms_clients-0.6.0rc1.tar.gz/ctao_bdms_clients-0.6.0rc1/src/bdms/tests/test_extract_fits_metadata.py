from astropy.io import fits

from bdms.extract_fits_metadata import (
    extract_metadata_from_data,
    extract_metadata_from_headers,
)


def test_extraction_correct_value_subarray_file(subarray_test_file):
    """Test the extraction of metadata from a FITS file."""
    with fits.open(subarray_test_file) as hdul:
        metadata_header = extract_metadata_from_headers(hdul, subarray_test_file)

    metadata_payload = extract_metadata_from_data(subarray_test_file)
    metadata_fits = {**metadata_header, **metadata_payload}

    assert len(metadata_fits) > 0, "No metadata found in the SUBARRAY FITS"

    expected_keys_in_fits_file = {
        "observatory": "CTA",
        "start_time": "2025-02-04T21:34:05",
        "end_time": "2025-02-04T21:43:12",
        "subarray_id": 0,
        "sb_id": 2000000066,
        "obs_id": 2000000200,
    }

    for key, value in expected_keys_in_fits_file.items():
        assert metadata_fits[key] == value, f"Expected key '{key}' not found."


def test_extraction_correct_value_tel_trigger_file(tel_trigger_test_file):
    """Test the extraction of metadata from a FITS file."""
    with fits.open(tel_trigger_test_file) as hdul:
        metadata_header = extract_metadata_from_headers(hdul, tel_trigger_test_file)

    metadata_payload = extract_metadata_from_data(tel_trigger_test_file)
    metadata_fits = {**metadata_header, **metadata_payload}

    assert len(metadata_fits) > 0, "No metadata found in the Telescope TRIGGER FITS"

    expected_keys_in_fits_file = {
        "observatory": "CTA",
        "start_time": "2025-02-04T21:34:05",
        "end_time": "2025-02-04T21:43:11",
        "tel_ids": [1],
        "sb_id": 2000000066,
        "obs_id": 2000000200,
    }

    for key, value in expected_keys_in_fits_file.items():
        assert metadata_fits[key] == value, f"Expected key '{key}' not found."


def test_extraction_correct_value_tel_events_file(tel_events_test_file):
    """Test the extraction of metadata from a FITS file."""
    with fits.open(tel_events_test_file) as hdul:
        metadata_header = extract_metadata_from_headers(hdul, tel_events_test_file)

    metadata_payload = extract_metadata_from_data(tel_events_test_file)
    metadata_fits = {**metadata_header, **metadata_payload}

    assert len(metadata_fits) > 0, "No metadata found in the Telescope EVENTS FITS"

    expected_keys_in_fits_file = {
        "observatory": "CTA",
        "start_time": "2025-04-01T15:25:02",
        "end_time": "2025-04-01T15:25:03",
        "sb_id": 0,
        "obs_id": 0,
    }

    for key, value in expected_keys_in_fits_file.items():
        assert metadata_fits[key] == value, f"Expected key '{key}' not found."


def test_extract_metadata_from_data_incorrect_header(tmp_path):
    """Test the extraction of metadata from an empty FITS file header."""
    fits_file_path = tmp_path / "empty_fits.fits.fz"
    hdul = fits.HDUList([fits.PrimaryHDU()])
    hdul.writeto(fits_file_path, checksum=True)

    with fits.open(fits_file_path) as hdul:
        metadata = extract_metadata_from_headers(hdul, fits_file_path)

    assert metadata == {}, "Expected empty metadata in the header"


def test_extract_metadata_from_data_incorrect_data(tmp_path):
    """Test the extraction of metadata from an empty FITS file data."""
    fits_file_path = tmp_path / "empty_fits.fits.fz"
    hdul = fits.HDUList([fits.PrimaryHDU()])
    hdul.writeto(fits_file_path, checksum=True)

    metadata = extract_metadata_from_data(fits_file_path)

    assert metadata == {}, "Expected empty metadata in the payload"


def test_missing_metadata_dl0(dummy_dl0_files, caplog, altered_metadata_schemas):
    subarray_file_path = dummy_dl0_files["subarray_file_path"]
    tel_event_path = dummy_dl0_files["tel_event_path"]
    trigger_event_path = dummy_dl0_files["trigger_event_path"]

    # extracting all the metadata (payload and header), and verify some metadata (required and optional) is actually missing

    with fits.open(subarray_file_path) as hdul:
        metadata_header = extract_metadata_from_headers(hdul, subarray_file_path)
    assert "missing_required_metadata" in metadata_header
    assert metadata_header["missing_required_metadata"]
    assert "missing_optional_metadata" in metadata_header
    assert metadata_header["missing_optional_metadata"]

    metadata_payload = extract_metadata_from_data(subarray_file_path)
    assert "missing_required_metadata" in metadata_payload
    assert metadata_payload["missing_required_metadata"]
    assert "missing_optional_metadata" in metadata_payload
    assert metadata_payload["missing_optional_metadata"]

    with fits.open(tel_event_path) as hdul:
        metadata_header = extract_metadata_from_headers(hdul, tel_event_path)
    assert "missing_required_metadata" in metadata_header
    assert metadata_header["missing_required_metadata"]
    assert "missing_optional_metadata" in metadata_header
    assert metadata_header["missing_optional_metadata"]

    metadata_payload = extract_metadata_from_data(tel_event_path)
    assert "missing_required_metadata" in metadata_payload
    assert metadata_payload["missing_required_metadata"]
    assert "missing_optional_metadata" in metadata_payload
    assert metadata_payload["missing_optional_metadata"]

    with fits.open(trigger_event_path) as hdul:
        metadata_header = extract_metadata_from_headers(hdul, trigger_event_path)
    assert "missing_required_metadata" in metadata_header
    assert metadata_header["missing_required_metadata"]
    assert "missing_optional_metadata" in metadata_header
    assert metadata_header["missing_optional_metadata"]

    metadata_payload = extract_metadata_from_data(trigger_event_path)
    assert "missing_required_metadata" in metadata_payload
    assert metadata_payload["missing_required_metadata"]
    assert "missing_optional_metadata" in metadata_payload
    assert metadata_payload["missing_optional_metadata"]

    # getting all the logs and inspect those in order to check
    # the warning and info logs are properly set for all the files and the relative missing metadata

    log_info = [[r.levelname, r.message] for r in caplog.records]

    # checking missing required metadata logs (warning)
    msg = "Missing warning log for a required metadata not found"
    assert [
        "WARNING",
        f"Required metadata not found in the header of the file {subarray_file_path}: DataStream.DUMMY_REQ_HEAD",
    ] in log_info, msg
    assert [
        "WARNING",
        f"Required metadata not found from the data of the file {subarray_file_path}: DataStream.DUMMY_REQ_PAY",
    ] in log_info, msg
    assert [
        "WARNING",
        f"Required metadata not found in the header of the file {tel_event_path}: DataStream.DUMMY_REQ_HEAD",
    ] in log_info, msg
    assert [
        "WARNING",
        f"Required metadata not found from the data of the file {tel_event_path}: DataStream.DUMMY_REQ_PAY",
    ] in log_info, msg
    assert [
        "WARNING",
        f"Required metadata not found in the header of the file {trigger_event_path}: DataStream.DUMMY_REQ_HEAD",
    ] in log_info, msg
    assert [
        "WARNING",
        f"Required metadata not found from the data of the file {trigger_event_path}: DataStream.DUMMY_REQ_PAY",
    ] in log_info, msg

    # checking missing optional metadata logs (info)
    msg = "Missing info log for an optional metadata not found"
    assert [
        "INFO",
        f"Optional metadata not found in the header of the file {subarray_file_path}: DataStream.DUMMY_OPT_HEAD",
    ] in log_info, msg
    assert [
        "INFO",
        f"Optional metadata not found from the data of the file {subarray_file_path}: DataStream.DUMMY_OPT_PAY",
    ] in log_info, msg
    assert [
        "INFO",
        f"Optional metadata not found in the header of the file {tel_event_path}: DataStream.DUMMY_OPT_HEAD",
    ] in log_info, msg
    assert [
        "INFO",
        f"Optional metadata not found from the data of the file {tel_event_path}: DataStream.DUMMY_OPT_PAY",
    ] in log_info, msg
    assert [
        "INFO",
        f"Optional metadata not found in the header of the file {trigger_event_path}: DataStream.DUMMY_OPT_HEAD",
    ] in log_info, msg
    assert [
        "INFO",
        f"Optional metadata not found from the data of the file {trigger_event_path}: DataStream.DUMMY_OPT_PAY",
    ] in log_info, msg
