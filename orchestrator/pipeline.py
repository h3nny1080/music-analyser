# -*- coding: utf-8 -*-
"""
Created on Sun May 10 13:01:50 2026

@author: Olive
"""

import asyncio
from ingestion.youtube import ingest_youtube
from ingestion.file_upload import ingest_file
from ingestion.detector import detect_input_type
from ingestion.streaming import find_youtube_candidates
from ingestion.quality_gate import IngestionError
from separation.demucs_agent import run_separation
from classification.clap_agent import classify_all_stems
from interaction.agent import build_selection_request
from .session_store import create_session
from .progress_store import set_progress, clear_progress


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

        # Streaming link — pause for user confirmation
        set_progress(sid, "ingestion", 5, "Fetching track metadata…")
        metadata, candidates = await asyncio.to_thread(
            find_youtube_candidates, input_data, source, spotify_token
        )
        return {
            "status":     "confirm",
            "session_id": sid,
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