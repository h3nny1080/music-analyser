# -*- coding: utf-8 -*-
"""
Created on Sun May 10 13:01:50 2026

@author: Olive
"""

import asyncio
from ingestion.youtube import ingest_youtube
from ingestion.file_upload import ingest_file
from ingestion.detector import detect_input_type
from ingestion.streaming import fetch_track_metadata
from ingestion.youtube_match_agent import search_youtube_for_track
from ingestion.soundcloud_match_agent import ingest_soundcloud
from ingestion.spotify_match_agent import search_spotify_track_on_youtube
from ingestion.quality_gate import IngestionError
from separation.demucs_agent import run_separation
from classification.clap_agent import classify_all_stems
from interaction.agent import build_selection_request
from .session_store import create_session
from .progress_store import set_progress, clear_progress


def _confirm_response(session_id: str, metadata: dict, candidates: list) -> dict:
    """Build the standard 'confirm' response sent to the frontend."""
    return {
        "status":     "confirm",
        "session_id": session_id,
        "metadata":   metadata,
        "candidates": [
            {
                "url":              c.url,
                "title":            c.title,
                "channel":          c.channel,
                "duration_seconds": c.duration_seconds,
                "thumbnail_url":    c.thumbnail_url,
            }
            for c in candidates
        ],
    }


async def run_full_pipeline(audio_obj, session_id: str) -> dict:
    try:
        # Stage 1 — separation
        set_progress(session_id, "separation", 10, "Separating stems with Demucs…")
        stem_collection = await asyncio.to_thread(run_separation, audio_obj)

        # Stage 2 — classification
        set_progress(session_id, "classification", 60, "Identifying instruments…")
        classifications = await asyncio.to_thread(classify_all_stems, stem_collection)

        # Stage 3 — build selection request
        set_progress(session_id, "classification", 90, "Finalising results…")
        selection_req = build_selection_request(classifications, stem_collection)
        create_session_data = {
            "classifications": classifications,
            "stem_collection": stem_collection,
        }
        from .session_store import _sessions
        _sessions[session_id] = create_session_data

        set_progress(session_id, "done", 100, "Analysis complete")

        return {
            "status":                "awaiting_selection",
            "session_id":            session_id,
            "confirmed_instruments": selection_req.confirmed_instruments,
            "unclear_stems":         selection_req.unclear_stems,
            "track_metadata":        selection_req.track_metadata,
        }

    except Exception as e:
        set_progress(session_id, "error", 0, str(e))
        raise


async def start_ingestion(
    input_data,
    filename:      str = "upload",
    spotify_token: str = None,
    session_id:    str = None,
) -> dict:
    import uuid
    sid = session_id or str(uuid.uuid4())

    try:
        if isinstance(input_data, bytes):
            set_progress(sid, "ingestion", 5, "Reading uploaded file…")
            audio = await asyncio.to_thread(ingest_file, input_data, filename)
            asyncio.create_task(run_full_pipeline(audio, sid))
            return {"status": "processing", "session_id": sid}

        source = detect_input_type(input_data)

        if source == "youtube":
            set_progress(sid, "ingestion", 5, "Downloading from YouTube…")
            audio = await asyncio.to_thread(ingest_youtube, input_data)
            asyncio.create_task(run_full_pipeline(audio, sid))
            return {"status": "processing", "session_id": sid}

        elif source == "spotify":
            set_progress(sid, "ingestion", 5, "Looking up Spotify track…")
            metadata, candidates = await asyncio.to_thread(
                search_spotify_track_on_youtube, input_data, spotify_token
            )
            return _confirm_response(
                sid,
                {
                    "title":            metadata.title,
                    "artist":           metadata.artist,
                    "album":            metadata.album,
                    "duration_seconds": metadata.duration_seconds,
                    "source_url":       metadata.source_url,
                    "platform":         "spotify",
                },
                candidates,
            )

        elif source == "apple_music":
            set_progress(sid, "ingestion", 5, "Looking up Apple Music track…")
            metadata = await asyncio.to_thread(
                fetch_track_metadata, input_data, "apple_music"
            )
            print(metadata)
            candidates = await asyncio.to_thread(
                search_youtube_for_track,
                metadata["title"], metadata["artist"], metadata.get("duration_seconds"),
            )
            if not candidates:
                raise IngestionError(
                    f"Could not find \"{metadata.get('artist', 'Unknown')} – {metadata.get('title', 'Unknown')}\" on YouTube. "
                    "Apple Music metadata was estimated from the URL and may be inaccurate — "
                    "try uploading an audio file directly."
                )
            return _confirm_response(sid, metadata, candidates)

        elif source == "soundcloud":
            set_progress(sid, "ingestion", 5, "Downloading from SoundCloud…")
            audio = await asyncio.to_thread(ingest_soundcloud, input_data)
            asyncio.create_task(run_full_pipeline(audio, sid))
            return {"status": "processing", "session_id": sid}

        elif source == "tidal":
            set_progress(sid, "ingestion", 5, "Looking up Tidal track…")
            metadata = await asyncio.to_thread(
                fetch_track_metadata, input_data, "tidal"
            )
            print(metadata)
            candidates = await asyncio.to_thread(
                search_youtube_for_track,
                metadata["title"], metadata["artist"], metadata.get("duration_seconds"),
            )
            if not candidates:
                raise IngestionError(
                    f"Could not find \"{metadata.get('artist', 'Unknown')} – {metadata.get('title', 'Unknown')}\" on YouTube. "
                    "Tidal does not expose public metadata — "
                    "try pasting a YouTube link or uploading the audio directly."
                )
            return _confirm_response(sid, metadata, candidates)

        else:
            raise IngestionError(f"Unsupported input source: {source!r}")

    except IngestionError as e:
        set_progress(sid, "error", 0, str(e))
        return {"status": "error", "message": str(e)}


async def confirm_youtube_match(confirmed_url: str, session_id: str) -> dict:
    try:
        set_progress(session_id, "ingestion", 15, "Downloading from YouTube…")
        audio = await asyncio.to_thread(ingest_youtube, confirmed_url)
        asyncio.create_task(run_full_pipeline(audio, session_id))
        return {"status": "processing", "session_id": session_id}
    except IngestionError as e:
        set_progress(session_id, "error", 0, str(e))
        return {"status": "error", "message": str(e)}