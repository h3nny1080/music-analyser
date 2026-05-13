# -*- coding: utf-8 -*-
"""
Created on Mon May 11 11:00:05 2026

@author: Olive
"""

import os
import shutil
import subprocess
import platform
import numpy as np
import music21
import re
from basic_pitch.inference import predict
from basic_pitch import ICASSP_2022_MODEL_PATH
from separation.models import Stem
from .models import OutputFile
from config.settings import settings

# Find LilyPond automatically via PATH rather than hardcoded path
_lilypond_path = (
    shutil.which("lilypond") or
    settings.lilypond_path
)

if _lilypond_path:
    music21.environment.set("lilypondPath", _lilypond_path)
else:
    raise EnvironmentError(
        "LilyPond not found. Make sure it is installed and on your PATH."
    )

MIDI_ONSET_THRESHOLD    = 0.5
MIDI_FRAME_THRESHOLD    = 0.3
MIDI_MIN_NOTE_LENGTH_MS = 80

def _sanitise_filename(name: str) -> str:
    return re.sub(r'[<>:"/\\|?*\[\]]', '_', name)

def stem_to_sheet_music(
    stem: Stem,
    instrument_label: str,
    output_dir: str,
    session_id: str,
) -> OutputFile:
    os.makedirs(output_dir, exist_ok=True)
    safe_label = _sanitise_filename(instrument_label.replace(" ", "_"))
    safe_id    = _sanitise_filename(session_id)
    midi_path  = os.path.join(output_dir, f"{safe_id}_{safe_label}.mid")
    pdf_path   = os.path.join(output_dir, f"{safe_id}_{safe_label}.pdf")

    _audio_to_midi(stem.audio, stem.sample_rate, midi_path)
    _midi_to_pdf(midi_path, pdf_path, instrument_label)

    # Verify the PDF was actually created
    if not os.path.exists(pdf_path):
        raise RuntimeError(
            f"LilyPond ran but did not produce a PDF at {pdf_path}. "
            "Check LilyPond is correctly installed."
        )

    return OutputFile(
        stem_name=stem.name,
        instrument_label=instrument_label,
        file_path=pdf_path,
        file_type="pdf",
        size_bytes=os.path.getsize(pdf_path),
    )


def _audio_to_midi(audio: np.ndarray, sample_rate: int, midi_path: str):
    """
    Convert audio to MIDI using Basic Pitch.
    Basic Pitch expects a file path on disk, not a raw numpy array.
    We write the audio to a temp WAV first, then pass that path.
    """
    import tempfile
    import soundfile as sf

    # Write numpy array to a temporary WAV file
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        sf.write(tmp_path, audio, sample_rate)

        model_output, midi_data, note_events = predict(
            tmp_path,                       # pass file path, not numpy array
            ICASSP_2022_MODEL_PATH,
            onset_threshold=MIDI_ONSET_THRESHOLD,
            frame_threshold=MIDI_FRAME_THRESHOLD,
            minimum_note_length=MIDI_MIN_NOTE_LENGTH_MS,
            melodia_trick=True,
            multiple_pitch_bends=False,
        )

        midi_data.write(midi_path)

    finally:
        # Always clean up the temp WAV
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


def _midi_to_pdf(midi_path: str, pdf_path: str, instrument_label: str):
    score = music21.converter.parse(midi_path)

    for part in score.parts:
        try:
            part.insert(0, music21.instrument.fromString(instrument_label))
        except music21.instrument.InstrumentException:
            part.insert(0, music21.instrument.Piano())

    # Use music21's built-in write method rather than LilypondConverter directly
    # This is the correct API for music21 v9+
    ly_path = pdf_path.replace(".pdf", ".ly")

    score.write("lily", fp=ly_path)

    # Now call LilyPond CLI directly on the generated .ly file
    result = subprocess.run(
        ["lilypond", "--pdf", "-o", pdf_path.replace(".pdf", ""), ly_path],
        capture_output=True,
        text=True,
        timeout=60,
        shell=(platform.system() == "Windows"),
    )

    # Clean up .ly file
    if os.path.exists(ly_path):
        os.unlink(ly_path)

    if result.returncode != 0:
        raise RuntimeError(
            f"LilyPond rendering failed:\n{result.stderr}"
        )

    if not os.path.exists(pdf_path):
        raise RuntimeError(
            f"LilyPond ran successfully but no PDF was found at {pdf_path}"
        )
        