# -*- coding: utf-8 -*-
"""
Created on Mon May 11 11:01:01 2026

@author: Olive
"""

import os
import re
from interaction.models import StemSelection, OutputChoice
from separation.models import StemCollection
from .sheet_music import stem_to_sheet_music
from .audio_export import stem_to_audio_file
from .models import OutputPackage, OutputFile


def _sanitise_filename(name: str) -> str:
    """Remove characters invalid in Windows file paths."""
    return re.sub(r'[<>:"/\\|?*\[\]]', '_', name)


def run_output_layer(
    selections: list[StemSelection],
    collection: StemCollection,
    session_id: str,
    audio_format: str = "wav",
    output_base_dir: str = "./outputs",
) -> OutputPackage:
    safe_session_id = _sanitise_filename(session_id)
    output_dir      = os.path.join(output_base_dir, safe_session_id)

    package = OutputPackage(
        session_id=session_id,
        track_metadata=collection.source_metadata,
    )

    for sel in selections:
        stem = collection.stems.get(sel.stem_name)
        if not stem:
            package.errors.append({
                "stem_name": sel.stem_name,
                "message":   f"Stem '{sel.stem_name}' not found in collection.",
            })
            continue

        try:
            if sel.output_choice in (OutputChoice.SHEET_MUSIC, OutputChoice.BOTH):
                pdf_file = stem_to_sheet_music(
                    stem, sel.instrument_label, output_dir, safe_session_id
                )
                package.files.append(pdf_file)

            if sel.output_choice in (OutputChoice.AUDIO_ISOLATE, OutputChoice.BOTH):
                audio_file = stem_to_audio_file(
                    stem, sel.instrument_label, output_dir,
                    safe_session_id, fmt=audio_format
                )
                package.files.append(audio_file)

        except Exception as e:
            package.errors.append({
                "stem_name": sel.stem_name,
                "message":   str(e),
            })

    return package