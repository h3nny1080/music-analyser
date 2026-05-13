# -*- coding: utf-8 -*-
"""
Created on Mon May 11 10:59:25 2026

@author: Olive
"""

from dataclasses import dataclass, field

@dataclass
class OutputFile:
    stem_name: str          # e.g. "guitar"
    instrument_label: str   # e.g. "acoustic guitar"
    file_path: str          # absolute path to the generated file
    file_type: str          # "pdf", "wav", "flac", "aiff", "midi"
    size_bytes: int

@dataclass
class OutputPackage:
    session_id: str
    track_metadata: dict
    files: list[OutputFile] = field(default_factory=list)
    errors: list[dict]      = field(default_factory=list)
    # errors: [{ stem_name, message }] — non-fatal, rest of package still valid