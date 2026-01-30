"""Functions to extract metadata from input files."""

import logging

import numpy as np
from protozfits import File

# Configure logger
logger = logging.getLogger(__name__)

# COMMON HEADER
start_time = "DataStream.DATE"

# COMMON DATA
origin = "DataStream.ORIGIN"
sb_id = "DataStream.sb_id"
obs_id = "DataStream.obs_id"

# -- FOR TEL_TRIG
tel_ids = "DataStream.tel_ids"

# -- FOR TEL_SUB
subarray_id = "DataStream.subarray_id"

METADATA_TEL = {
    "HEADER": {
        "required": {
            "observatory": origin,
            "start_time": start_time,
            "end_time": "Events.DATEEND",
        },
        "optional": {},
    },
    "PAYLOAD": {
        "required": {
            "sb_id": sb_id,
            "obs_id": obs_id,
        },
        "optional": {},
    },
}

METADATA_SUB = {
    "HEADER": {
        "required": {
            "observatory": origin,
            "start_time": start_time,
            "end_time": "SubarrayEvents.DATEEND",
        },
        "optional": {},
    },
    "PAYLOAD": {
        "required": {
            "subarray_id": subarray_id,
            "sb_id": sb_id,
            "obs_id": obs_id,
        },
        "optional": {},
    },
}

METADATA_TRIG = {
    "HEADER": {
        "required": {
            "observatory": origin,
            "start_time": start_time,
            "end_time": "Triggers.DATEEND",
        },
        "optional": {},
    },
    "PAYLOAD": {
        "required": {
            "tel_ids": tel_ids,
            "sb_id": sb_id,
            "obs_id": obs_id,
        },
        "optional": {},
    },
}

#: Mapping from DataStream.PBFHEAD to the metadata items we want to collect
METADATA_SCHEMAS = {
    "DL0v1.Trigger.DataStream": METADATA_TRIG,
    "DL0v1.Subarray.DataStream": METADATA_SUB,
    "DL0v1.Telescope.DataStream": METADATA_TEL,
}


def _extract_metadata_items_generic(
    schema_items,
    source,
    path,
    metadata,
    missing_key,
    log_func,
    get_metadata_func,
    log_missing_metadata_msg,
):
    for value_name, metadata_path in schema_items.items():
        part1, part2 = metadata_path.split(".")
        value = get_metadata_func(source, part1, part2)
        if value is not None:
            metadata[value_name] = value
            logger.debug(
                "Value '%s' from '%s' extracted. (renamed as '%s')",
                part2,
                part1,
                value_name,
            )
        else:
            metadata[missing_key] = True
            log_func(log_missing_metadata_msg, path, metadata_path)


def extract_metadata_from_headers(hdul, path):
    """Extract metadata from FITS headers of hdul."""
    all_headers = {}
    for hdu in hdul:
        if hdu.is_image:
            continue
        all_headers[hdu.name] = dict(hdu.header)

    if "DataStream" not in all_headers:
        logger.error("No DataStream HDU found in the FITS file.")
        return {}

    pbfhead = all_headers["DataStream"]["PBFHEAD"]
    schema = METADATA_SCHEMAS.get(pbfhead)
    if schema is None:
        logger.error(
            "The PBFHEAD %r does not correspond to any known FITS type.", pbfhead
        )
        return {}

    logger.debug("Headers extracted: %s", all_headers.keys())

    def get_header_metadata(headers, extname, header_key):
        return headers.get(extname, {}).get(header_key, None)

    metadata = {}
    _extract_metadata_items_generic(
        schema["HEADER"]["required"],
        all_headers,
        path,
        metadata,
        "missing_required_metadata",
        logger.warning,
        get_header_metadata,
        "Required metadata not found in the header of the file %s: %s",
    )
    _extract_metadata_items_generic(
        schema["HEADER"]["optional"],
        all_headers,
        path,
        metadata,
        "missing_optional_metadata",
        logger.info,
        get_header_metadata,
        "Optional metadata not found in the header of the file %s: %s",
    )
    return metadata


def extract_metadata_from_data(path):
    """Extract metadata from zFITS payload in path."""
    with File(path) as f:
        if not hasattr(f, "DataStream"):
            return {}

        pbfhead = f.DataStream.header["PBFHEAD"]
        schema = METADATA_SCHEMAS.get(pbfhead)
        if schema is None:
            logger.error(
                "The PBFHEAD %r does not correspond to any known FITS type.", pbfhead
            )
            return {}

        def get_header_data(file_obj, hdu, column):
            row = getattr(file_obj, hdu)[0]
            if hasattr(row, column):
                value = getattr(row, column)
                if isinstance(value, np.ndarray):
                    return value.tolist()
                return value
            return None

        metadata = {}
        _extract_metadata_items_generic(
            schema["PAYLOAD"]["required"],
            f,
            path,
            metadata,
            "missing_required_metadata",
            logger.warning,
            get_header_data,
            "Required metadata not found from the data of the file %s: %s",
        )
        _extract_metadata_items_generic(
            schema["PAYLOAD"]["optional"],
            f,
            path,
            metadata,
            "missing_optional_metadata",
            logger.info,
            get_header_data,
            "Optional metadata not found from the data of the file %s: %s",
        )

        return metadata
