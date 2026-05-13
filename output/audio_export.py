# -*- coding: utf-8 -*-
"""
Created on Mon May 11 11:00:33 2026

@author: Olive
"""

import os
import soundfile as sf
import re
from separation.models import Stem, StemCollection
from interaction.models import StemSelection
from .models import OutputFile

SUPPORTED_FORMATS = {"wav", "flac", "aiff"}
DEFAULT_FORMAT     = "wav"
SUBTYPE_MAP        = {
    "wav":  "PCM_24",
    "flac": "PCM_24",
    "aiff": "PCM_24",
}

def _sanitise_filename(name: str) -> str:
    return re.sub(r'[<>:"/\\|?*\[\]]', '_', name)

def stem_to_audio_file(
    stem: Stem,
    instrument_label: str,
    output_dir: str,
    session_id: str,
    fmt: str = DEFAULT_FORMAT,
) -> OutputFile:
    """
    Export a stem as a named audio file.
    Returns an OutputFile pointing to the exported file.
    """
    if fmt not in SUPPORTED_FORMATS:
        raise ValueError(f"Unsupported format '{fmt}'. Choose from: {SUPPORTED_FORMATS}")

    os.makedirs(output_dir, exist_ok=True)
    safe_label = _sanitise_filename(instrument_label.replace(" ", "_"))
    safe_id    = _sanitise_filename(session_id)
    file_path  = os.path.join(output_dir, f"{safe_id}_{safe_label}.{fmt}")

    sf.write(file_path, stem.audio, stem.sample_rate, subtype=SUBTYPE_MAP[fmt])

    return OutputFile(
        stem_name=stem.name,
        instrument_label=instrument_label,
        file_path=file_path,
        file_type=fmt,
        size_bytes=os.path.getsize(file_path),
    )