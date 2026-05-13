# -*- coding: utf-8 -*-
"""
Created on Mon May 11 10:44:32 2026

@author: Olive
"""

import os
import numpy as np
import soundfile as sf
from .models import StemCollection, Stem

SUPPORTED_FORMATS = {"wav", "flac", "aiff"}

def export_stem(
    stem: Stem,
    output_dir: str,
    fmt: str = "wav",
    prefix: str = "",
) -> str:
    """
    Write a single Stem to disk as a WAV/FLAC/AIFF file.
    Returns the path to the written file.
    """
    if fmt not in SUPPORTED_FORMATS:
        raise ValueError(f"Unsupported format '{fmt}'. Choose from: {SUPPORTED_FORMATS}")

    os.makedirs(output_dir, exist_ok=True)
    filename = f"{prefix}{stem.name}.{fmt}" if prefix else f"{stem.name}.{fmt}"
    path = os.path.join(output_dir, filename)

    # soundfile expects (samples,) for mono
    sf.write(path, stem.audio, stem.sample_rate, subtype="PCM_24")
    return path


def export_selected_stems(
    collection: StemCollection,
    stem_names: list[str],
    output_dir: str,
    fmt: str = "wav",
) -> dict[str, str]:
    """
    Export a subset of stems chosen by the user.
    Returns { stem_name: file_path } for each exported stem.
    """
    paths = {}
    for name in stem_names:
        if name not in collection.stems:
            raise ValueError(f"Unknown stem: '{name}'")
        stem = collection.stems[name]
        paths[name] = export_stem(stem, output_dir, fmt=fmt)
    return paths