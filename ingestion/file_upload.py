# -*- coding: utf-8 -*-
"""
Created on Mon May 11 10:25:10 2026

@author: Olive
"""

import os
import tempfile
from .normaliser import normalise_file
from .quality_gate import IngestionError
from .models import AudioObject

SUPPORTED_EXTENSIONS = {".mp3", ".wav", ".flac", ".aiff", ".aif", ".ogg", ".m4a"}
MAX_FILE_BYTES = 200 * 1024 * 1024   # 200 MB hard limit

def ingest_file(
    file_bytes: bytes,
    filename: str = "upload",
) -> AudioObject:
    """
    Accept raw audio bytes (from an API file upload),
    write to a temp file, and normalise.
    """
    # Check file size
    if len(file_bytes) > MAX_FILE_BYTES:
        raise IngestionError(
            f"File too large ({len(file_bytes) // (1024*1024)}MB). "
            f"Maximum is {MAX_FILE_BYTES // (1024*1024)}MB."
        )

    # Check extension
    ext = os.path.splitext(filename)[1].lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise IngestionError(
            f"Unsupported file type '{ext}'. "
            f"Supported formats: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
        )

    # Write bytes to temp file so librosa/ffmpeg can read it
    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as f:
        f.write(file_bytes)
        tmp_path = f.name

    try:
        metadata = {
            "title":      os.path.splitext(filename)[0],
            "source_url": None,
            "platform":   "upload",
            "filename":   filename,
        }
        return normalise_file(tmp_path, source_type="upload", metadata=metadata)
    finally:
        os.unlink(tmp_path)