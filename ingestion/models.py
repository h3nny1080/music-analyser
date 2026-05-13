# -*- coding: utf-8 -*-
"""
Created on Sat May  9 15:55:05 2026

@author: Olive
"""

from dataclasses import dataclass, field
import numpy as np

@dataclass
class AudioObject:
    audio: np.ndarray        # float32 mono array
    sample_rate: int         # always 44100
    duration_seconds: float
    source_type: str         # "youtube" | "streaming" | "upload"
    metadata: dict = field(default_factory=dict)
    # e.g. {"title": "...", "artist": "...", "source_url": "..."}