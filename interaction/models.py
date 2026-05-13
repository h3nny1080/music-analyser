# -*- coding: utf-8 -*-
"""
Created on Mon May 11 10:47:41 2026

@author: Olive
"""

from dataclasses import dataclass, field
from enum import Enum

class OutputChoice(Enum):
    SHEET_MUSIC   = "sheet_music"
    AUDIO_ISOLATE = "audio_isolate"
    BOTH          = "both"

@dataclass
class StemSelection:
    stem_name: str          # e.g. "guitar"
    instrument_label: str   # e.g. "acoustic guitar" — confirmed or user-chosen
    output_choice: OutputChoice

@dataclass
class UserSelectionRequest:
    """Sent to the frontend — describes what to show the user."""
    confirmed_instruments: list[dict]   # [{ stem, label, confidence }]
    unclear_stems: list[dict]           # [{ stem, top3_labels }]
    track_metadata: dict                # title, artist

@dataclass
class UserSelectionResponse:
    """Received back from the frontend after the user makes choices."""
    selections: list[StemSelection]     # one per instrument the user wants