# -*- coding: utf-8 -*-
"""
Created on Mon May 11 10:44:14 2026

@author: Olive
"""

import os
import tempfile
import numpy as np
import soundfile as sf
import torch
from demucs.pretrained import get_model
from demucs.apply import apply_model
from demucs.audio import AudioFile, save_audio

from .models import Stem, StemCollection, STEM_NAMES
from ingestion.models import AudioObject

MODEL_NAME = "htdemucs_6s"     # 6-stem variant
SILENCE_RMS = 0.001            # stems below this are considered empty

_model_cache = None            # module-level cache — load once, reuse

def _get_model():
    global _model_cache
    if _model_cache is None:
        _model_cache = get_model(MODEL_NAME)
        _model_cache.eval()
        if torch.cuda.is_available():
            _model_cache.cuda()
    return _model_cache


def run_separation(audio_obj: AudioObject) -> StemCollection:
    """
    Separate an AudioObject into 6 stems using Demucs htdemucs_6s.
    Returns a StemCollection containing a Stem for each source.
    """
    model = _get_model()
    device = "cuda" if torch.cuda.is_available() else "cpu"

    # Demucs expects a stereo tensor: shape [1, 2, samples]
    # Our AudioObject is mono — duplicate the channel
    mono = audio_obj.audio                            # (samples,)
    stereo = np.stack([mono, mono], axis=0)           # (2, samples)
    waveform = torch.tensor(stereo, dtype=torch.float32).unsqueeze(0).to(device)

    # Run separation
    with torch.no_grad():
        sources = apply_model(
            model,
            waveform,
            device=device,
            shifts=1,          # 1 random shift = good quality, fast-ish
            split=True,        # split long tracks into chunks to save VRAM
            overlap=0.25,      # 25% overlap between chunks
            progress=False,
        )
    # sources shape: [1, num_stems, 2, samples]
    sources = sources.squeeze(0).cpu().numpy()        # (num_stems, 2, samples)

    stems = {}
    for i, name in enumerate(model.sources):          # model.sources = STEM_NAMES
        # Mix stereo down to mono by averaging channels
        stem_mono = sources[i].mean(axis=0)           # (samples,)
        rms = float(np.sqrt(np.mean(stem_mono ** 2)))

        stems[name] = Stem(
            name=name,
            audio=stem_mono,
            sample_rate=audio_obj.sample_rate,
            duration_seconds=round(len(stem_mono) / audio_obj.sample_rate, 2),
            rms_energy=rms,
        )

    active = [name for name, stem in stems.items() if stem.rms_energy > SILENCE_RMS]

    return StemCollection(
        stems=stems,
        source_metadata=audio_obj.metadata,
        active_stems=active,
    )