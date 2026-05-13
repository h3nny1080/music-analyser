# -*- coding: utf-8 -*-
"""
Created on Mon May 11 10:28:31 2026

@author: Olive
"""

import numpy as np
import pytest
from ingestion import detect_input_type, IngestionError
from ingestion.normaliser import normalise_file
from ingestion.quality_gate import run_quality_gate
import tempfile, os
import soundfile as sf

# --- detector tests ---

def test_detect_youtube():
    assert detect_input_type("https://www.youtube.com/watch?v=dQw4w9WgXcQ") == "youtube"
    assert detect_input_type("https://youtu.be/dQw4w9WgXcQ") == "youtube"

def test_detect_spotify():
    assert detect_input_type("https://open.spotify.com/track/4uLU6hMCjMI75M1A2tKUQC") == "spotify"

def test_detect_soundcloud():
    assert detect_input_type("https://soundcloud.com/artist/track-name") == "soundcloud"

def test_detect_file_fallback():
    assert detect_input_type("mysong.mp3") == "file"
    assert detect_input_type("not a url at all") == "file"

# --- quality gate tests ---

def test_quality_gate_too_short():
    short_audio = np.random.randn(44100 * 5).astype(np.float32)  # 5 seconds
    with pytest.raises(IngestionError, match="too short"):
        run_quality_gate(short_audio, duration=5.0)

def test_quality_gate_silent():
    silent = np.zeros(44100 * 30, dtype=np.float32)
    with pytest.raises(IngestionError, match="silent"):
        run_quality_gate(silent, duration=30.0)

def test_quality_gate_passes():
    good_audio = np.random.randn(44100 * 30).astype(np.float32)
    run_quality_gate(good_audio, duration=30.0)  # should not raise

# --- normaliser tests ---

def test_normalise_produces_correct_sample_rate():
    # Create a 30s WAV at 22050 Hz (wrong rate) — normaliser must resample
    audio = np.random.randn(22050 * 30).astype(np.float32)
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        sf.write(f.name, audio, 22050)
        tmp = f.name
    try:
        obj = normalise_file(tmp, source_type="upload", metadata={})
        assert obj.sample_rate == 44100
        assert obj.audio.dtype == np.float32
    finally:
        os.unlink(tmp)

def test_normalise_peak_level():
    audio = np.random.randn(44100 * 30).astype(np.float32) * 0.1
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        sf.write(f.name, audio, 44100)
        tmp = f.name
    try:
        obj = normalise_file(tmp, source_type="upload", metadata={})
        peak_db = 20 * np.log10(np.max(np.abs(obj.audio)))
        assert -2.0 < peak_db <= 0.0   # within 1 dB of -1 dBFS target
    finally:
        os.unlink(tmp)