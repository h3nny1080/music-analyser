# -*- coding: utf-8 -*-
"""
Created on Sun May 10 12:58:15 2026

@author: Olive
"""

import numpy as np

MIN_DURATION_S   = 10.0
MAX_DURATION_S   = 900.0   # 15 minutes
SILENCE_THRESHOLD = 0.001  # peak amplitude below this = silent

class IngestionError(ValueError):
    """Raised when audio fails a quality check."""
    pass

def run_quality_gate(audio: np.ndarray, duration: float) -> None:
    if duration < MIN_DURATION_S:
        raise IngestionError(
            f"Audio is too short ({duration:.1f}s). "
            f"Minimum length is {MIN_DURATION_S}s."
        )
    if duration > MAX_DURATION_S:
        raise IngestionError(
            f"Audio is too long ({duration:.0f}s). "
            f"Maximum length is {int(MAX_DURATION_S // 60)} minutes."
        )
    if np.max(np.abs(audio)) < SILENCE_THRESHOLD:
        raise IngestionError(
            "Audio appears to be completely silent. "
            "Please check the source file or link."
        )