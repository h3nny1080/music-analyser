# -*- coding: utf-8 -*-
"""
Created on Mon May 11 12:53:58 2026

@author: Olive
"""

import pytest
import asyncio
import shutil
import numpy as np
import soundfile as sf
import tempfile
import os

from ingestion.models import AudioObject
from separation.demucs_agent import run_separation
from classification.clap_agent import classify_all_stems
from interaction.agent import build_selection_request
from interaction.models import StemSelection, OutputChoice
from output.router import run_output_layer


# ── Fixtures ────────────────────────────────────────────────────────────────

@pytest.fixture
def sine_audio_object():
    """
    Minimal AudioObject: 30 seconds of a 440 Hz sine wave (A4).
    Simple enough that Demucs and CLAP can process it quickly.
    """
    sr       = 44100
    duration = 30
    t        = np.linspace(0, duration, sr * duration, endpoint=False)
    audio    = (np.sin(2 * np.pi * 440 * t) * 0.5).astype(np.float32)

    return AudioObject(
        audio=audio,
        sample_rate=sr,
        duration_seconds=duration,
        source_type="test",
        metadata={"title": "Test Tone", "artist": "pytest"},
    )


@pytest.fixture
def real_audio_object(tmp_path):
    """
    If a test WAV exists at tests/fixtures/test_track.wav, use it.
    Otherwise fall back to the sine fixture.
    Swap in a real track here for more meaningful classification tests.
    """
    fixture_path = os.path.join("tests", "fixtures", "test_track.wav")
    if not os.path.exists(fixture_path):
        pytest.skip("No test fixture at tests/fixtures/test_track.wav — skipping real audio test")

    import librosa
    audio, _ = librosa.load(fixture_path, sr=44100, mono=True)
    return AudioObject(
        audio=audio,
        sample_rate=44100,
        duration_seconds=len(audio) / 44100,
        source_type="test",
        metadata={"title": "Fixture Track", "artist": "test"},
    )


# ── Ingestion unit tests ─────────────────────────────────────────────────────

class TestIngestionLayer:
    def test_detector_youtube(self):
        from ingestion.detector import detect_input_type
        assert detect_input_type("https://www.youtube.com/watch?v=dQw4w9WgXcQ") == "youtube"

    def test_detector_spotify(self):
        from ingestion.detector import detect_input_type
        assert detect_input_type("https://open.spotify.com/track/abc123") == "spotify"

    def test_detector_file_fallback(self):
        from ingestion.detector import detect_input_type
        assert detect_input_type("mysong.mp3") == "file"

    def test_quality_gate_rejects_silence(self):
        from ingestion.quality_gate import run_quality_gate, IngestionError
        silent = np.zeros(44100 * 30, dtype=np.float32)
        with pytest.raises(IngestionError, match="silent"):
            run_quality_gate(silent, 30.0)

    def test_quality_gate_rejects_short(self):
        from ingestion.quality_gate import run_quality_gate, IngestionError
        short = np.random.randn(44100 * 5).astype(np.float32)
        with pytest.raises(IngestionError, match="short"):
            run_quality_gate(short, 5.0)

    def test_normaliser_resamples_to_44100(self, tmp_path):
        from ingestion.normaliser import normalise_file
        audio = np.random.randn(22050 * 30).astype(np.float32)
        path  = str(tmp_path / "test.wav")
        sf.write(path, audio, 22050)
        obj = normalise_file(path, "test", {})
        assert obj.sample_rate == 44100

    def test_normaliser_peak_level(self, tmp_path):
        from ingestion.normaliser import normalise_file
        audio = np.random.randn(44100 * 30).astype(np.float32) * 0.05
        path  = str(tmp_path / "test.wav")
        sf.write(path, audio, 44100)
        obj = normalise_file(path, "test", {})
        peak_db = 20 * np.log10(np.max(np.abs(obj.audio)))
        assert -2.0 < peak_db <= 0.0


# ── Separation tests ─────────────────────────────────────────────────────────

class TestSeparationLayer:
    def test_separation_returns_six_stems(self, sine_audio_object):
        collection = run_separation(sine_audio_object)
        assert set(collection.stems.keys()) == {
            "vocals", "drums", "bass", "guitar", "piano", "other"
        }

    def test_separation_preserves_sample_rate(self, sine_audio_object):
        collection = run_separation(sine_audio_object)
        for stem in collection.stems.values():
            assert stem.sample_rate == 44100

    def test_separation_active_stems_populated(self, sine_audio_object):
        collection = run_separation(sine_audio_object)
        # A sine wave is very simple — at least one stem should be active
        assert len(collection.active_stems) >= 1

    def test_separation_metadata_passthrough(self, sine_audio_object):
        collection = run_separation(sine_audio_object)
        assert collection.source_metadata["title"] == "Test Tone"

    def test_stem_audio_length_matches_source(self, sine_audio_object):
        collection = run_separation(sine_audio_object)
        expected_samples = len(sine_audio_object.audio)
        for stem in collection.stems.values():
            # Allow ±1% tolerance for Demucs padding
            assert abs(len(stem.audio) - expected_samples) < expected_samples * 0.01


# ── Classification tests ──────────────────────────────────────────────────────

class TestClassificationLayer:
    def test_classification_returns_result_per_active_stem(self, sine_audio_object):
        collection      = run_separation(sine_audio_object)
        classifications = classify_all_stems(collection)
        for stem_name in collection.active_stems:
            assert stem_name in classifications

    def test_classification_result_has_required_fields(self, sine_audio_object):
        collection      = run_separation(sine_audio_object)
        classifications = classify_all_stems(collection)
        for result in classifications.values():
            assert result.top_label
            assert 0.0 <= result.top_confidence <= 1.0
            assert isinstance(result.needs_user_input, bool)
            assert len(result.matches) > 0

    def test_classification_matches_ranked(self, sine_audio_object):
        collection      = run_separation(sine_audio_object)
        classifications = classify_all_stems(collection)
        for result in classifications.values():
            scores = [m.confidence for m in result.matches]
            assert scores == sorted(scores, reverse=True)

    @pytest.mark.skipif(
        not os.path.exists("tests/fixtures/test_track.wav"),
        reason="No fixture track available"
    )
    def test_real_track_classifies_plausibly(self, real_audio_object):
        """
        Smoke test on a real track — checks that CLAP returns
        something plausible, not that it's perfectly accurate.
        Replace test_track.wav with a piano or guitar solo for
        the most meaningful results.
        """
        collection      = run_separation(real_audio_object)
        classifications = classify_all_stems(collection)
        assert len(classifications) > 0
        for result in classifications.values():
            assert result.top_confidence > 0.0


# ── Interaction layer tests ───────────────────────────────────────────────────

class TestInteractionLayer:
    def test_build_selection_request_structure(self, sine_audio_object):
        collection      = run_separation(sine_audio_object)
        classifications = classify_all_stems(collection)
        req             = build_selection_request(classifications, collection)

        assert isinstance(req.confirmed_instruments, list)
        assert isinstance(req.unclear_stems, list)
        assert isinstance(req.track_metadata, dict)

    def test_process_user_response_validates_stem_names(self, sine_audio_object):
        from interaction.agent import process_user_response
        from interaction.models import UserSelectionResponse

        collection      = run_separation(sine_audio_object)
        classifications = classify_all_stems(collection)

        bad_response = UserSelectionResponse(selections=[
            StemSelection(
                stem_name="nonexistent_stem",
                instrument_label="piano",
                output_choice=OutputChoice.AUDIO_ISOLATE,
            )
        ])
        with pytest.raises(ValueError, match="Unknown stem"):
            process_user_response(bad_response, classifications)

    def test_process_user_response_rejects_empty(self, sine_audio_object):
        from interaction.agent import process_user_response
        from interaction.models import UserSelectionResponse

        collection      = run_separation(sine_audio_object)
        classifications = classify_all_stems(collection)

        with pytest.raises(ValueError, match="No instruments selected"):
            process_user_response(
                UserSelectionResponse(selections=[]),
                classifications,
            )


# ── Output layer tests ────────────────────────────────────────────────────────

class TestOutputLayer:
    def test_audio_export_creates_wav(self, sine_audio_object, tmp_path):
        from output.audio_export import stem_to_audio_file

        collection = run_separation(sine_audio_object)
        stem       = collection.stems["other"]

        output_file = stem_to_audio_file(
            stem,
            instrument_label="test instrument",
            output_dir=str(tmp_path),
            session_id="test-session",
            fmt="wav",
        )
        assert os.path.exists(output_file.file_path)
        assert output_file.file_type == "wav"
        assert output_file.size_bytes > 0

    def test_audio_export_creates_flac(self, sine_audio_object, tmp_path):
        from output.audio_export import stem_to_audio_file

        collection = run_separation(sine_audio_object)
        stem       = collection.stems["other"]

        output_file = stem_to_audio_file(
            stem, "test instrument", str(tmp_path), "test-session", fmt="flac"
        )
        assert output_file.file_type == "flac"
        assert os.path.exists(output_file.file_path)

    def test_output_router_audio_isolate(self, sine_audio_object, tmp_path):
        collection      = run_separation(sine_audio_object)
        classifications = classify_all_stems(collection)

        # Pick the first active stem
        stem_name = collection.active_stems[0]
        label     = classifications[stem_name].top_label

        selections = [
            StemSelection(
                stem_name=stem_name,
                instrument_label=label,
                output_choice=OutputChoice.AUDIO_ISOLATE,
            )
        ]

        import os
        os.environ["OUTPUT_BASE_DIR"] = str(tmp_path)

        package = run_output_layer(
            selections, collection, "test-session"
        )

        assert len(package.files) == 1
        assert package.files[0].file_type in ("wav", "flac", "aiff")
        assert len(package.errors) == 0

    @pytest.mark.skipif(
        shutil.which("lilypond") is None,
        reason="LilyPond not installed"
        )
    def test_output_router_sheet_music(self, sine_audio_object, tmp_path):
        collection = run_separation(sine_audio_object)
        stem_name  = collection.active_stems[0]
    
        selections = [
            StemSelection(
                stem_name=stem_name,
                instrument_label="piano",
                output_choice=OutputChoice.SHEET_MUSIC,
            )
        ]
    
        package = run_output_layer(
            selections,
            collection,
            "test-session-pdf",
            output_base_dir=str(tmp_path),   # pass tmp_path explicitly
        )
        
        print(package.errors)
    
        assert len(package.errors) == 0, f"Errors: {package.errors}"
        assert len(package.files) > 0
        assert any(f.file_type == "pdf" for f in package.files)


# ── Full pipeline integration test ───────────────────────────────────────────

class TestFullPipeline:
    @pytest.mark.asyncio
    async def test_pipeline_runs_end_to_end(self, sine_audio_object, tmp_path):
        """
        Runs the full pipeline from AudioObject to OutputPackage
        without touching the HTTP layer.
        """
        from orchestrator.pipeline import run_full_pipeline
        from orchestrator.session_store import get_session

        session_id = "e2e-test-session"
        result     = await run_full_pipeline(sine_audio_object, session_id)

        assert result["status"] == "awaiting_selection"
        assert result["session_id"] == session_id
        assert isinstance(result["confirmed_instruments"], list)
        assert isinstance(result["unclear_stems"], list)

        # Session should be stored
        session = get_session(session_id)
        assert session is not None
        assert "classifications" in session
        assert "stem_collection" in session

    @pytest.mark.asyncio
    async def test_pipeline_progress_updates(self, sine_audio_object):
        from orchestrator.pipeline import run_full_pipeline
        from orchestrator.progress_store import get_progress

        session_id = "progress-test-session"
        await run_full_pipeline(sine_audio_object, session_id)

        prog = get_progress(session_id)
        assert prog["percent"] == 100
        assert prog["stage"] == "done"