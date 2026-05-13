# -*- coding: utf-8 -*-
"""
Created on Mon May 11 10:36:27 2026

@author: Olive
"""

from dataclasses import dataclass, field

@dataclass
class InstrumentMatch:
    label: str          # e.g. "acoustic guitar"
    confidence: float   # cosine similarity score, 0.0–1.0
    is_confident: bool  # True if above the confidence threshold

@dataclass
class ClassificationResult:
    stem_name: str                        # "vocals", "guitar", etc.
    matches: list[InstrumentMatch]        # ranked, best match first
    top_label: str                        # shortcut to matches[0].label
    top_confidence: float                 # shortcut to matches[0].confidence
    needs_user_input: bool                # True if top score below threshold