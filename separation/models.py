# -*- coding: utf-8 -*-
"""
Created on Mon May 11 10:43:24 2026

@author: Olive
"""

from dataclasses import dataclass, field
import numpy as np

STEM_NAMES = ["vocals", "drums", "bass", "guitar", "piano", "other"]

@dataclass
class Stem:
    name: str               # one of STEM_NAMES
    audio: np.ndarray       # float32 mono, 44100 Hz
    sample_rate: int        # always 44100
    duration_seconds: float
    rms_energy: float       # root mean square — used to detect silent/empty stems

@dataclass
class StemCollection:
    stems: dict             # { "vocals": Stem, "drums": Stem, ... }
    source_metadata: dict   # passed through from AudioObject.metadata
    active_stems: list      # stem names where rms_energy > silence threshold