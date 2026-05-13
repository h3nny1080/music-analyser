# -*- coding: utf-8 -*-
"""
Created on Sun May 10 12:56:43 2026

@author: Olive
"""

import os
import numpy as np
import librosa
import soundfile as sf
import tempfile
from .quality_gate import run_quality_gate
from .models import AudioObject

TARGET_SR  = 44100
PAD_SECS   = 0.2      # padding added each end to avoid Demucs edge artefacts
PEAK_DBFS  = -1.0     # normalise to -1 dBFS headroom
TOP_DB     = 30       # silence threshold for trimming (dB below peak)

def normalise_file(
    path: str,
    source_type: str,
    metadata: dict,
) -> AudioObject:
    """
    Load any audio file, normalise it to a clean AudioObject.
    - Resamples to 44100 Hz mono float32
    - Peak-normalises to -1 dBFS
    - Trims leading/trailing silence
    - Pads 0.2s each end
    - Runs quality gate (raises IngestionError on failure)
    """
    # Load + resample to mono 44100 Hz
    audio, _ = librosa.load(path, sr=TARGET_SR, mono=True, dtype=np.float32)

    # Peak normalise
    peak = np.max(np.abs(audio))
    if peak > 0:
        target_linear = 10 ** (PEAK_DBFS / 20)
        audio = audio / peak * target_linear

    # Trim silence from both ends
    audio, _ = librosa.effects.trim(
        audio, top_db=TOP_DB, frame_length=512, hop_length=128
    )

    # Pad to prevent Demucs edge artefacts
    pad_samples = int(PAD_SECS * TARGET_SR)
    audio = np.pad(audio, (pad_samples, pad_samples))

    duration = len(audio) / TARGET_SR

    # Quality checks — raises IngestionError on failure
    run_quality_gate(audio, duration)

    return AudioObject(
        audio=audio,
        sample_rate=TARGET_SR,
        duration_seconds=round(duration, 2),
        source_type=source_type,
        metadata=metadata,
    )