"""Utility functions for fw-meta."""

import re
import string

from fw_utils import flatten_dotdict


def sanitize_label(value: str) -> str:
    """Sanitize and truncate labels for filesystem dir/filename compatibility."""
    # replace '*' with 'star' (to retain eg. DICOM MR T2* domain context)
    value = re.sub(r"\*", r"star", value)
    # replace any occurrences of (one or more) invalid chars w/ an underscore
    unprintable = [chr(c) for c in range(128) if chr(c) not in string.printable]
    invalid_chars = "*/:<>?\\|\t\n\r\x0b\x0c" + "".join(unprintable)
    value = re.sub(rf"[{re.escape(invalid_chars):s}]+", "_", value)
    # truncate to 255 chars
    value = value[:255]
    # drop ending dots (azure limitation)
    value = value.rstrip(".")
    return value


def sanitize_values(value: dict) -> dict:
    """Sanitize container label and file name fields to be filesystem-safe."""
    flat = flatten_dotdict(value)
    for key, val in list(flat.items()):
        if "info" in key:  # allow exporting via path=file.info.path (=custom/path)
            continue
        if isinstance(val, str):
            flat[key] = sanitize_label(val)
        if isinstance(val, list):  # eg. tags
            flat[key] = [sanitize_label(v) for v in val]
    return flat
