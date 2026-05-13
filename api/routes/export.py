# -*- coding: utf-8 -*-
"""
Created on Mon May 11 11:01:39 2026

@author: Olive
"""

import os
from fastapi import APIRouter
from fastapi.responses import FileResponse, JSONResponse
from orchestrator.session_store import get_session, delete_session
from interaction.models import StemSelection, OutputChoice
from output.router import run_output_layer

router = APIRouter()


@router.post("/export/{session_id}")
async def export(session_id: str, payload: dict):
    """
    Trigger the output layer for a confirmed session.
    Returns metadata about the generated files with download URLs.
    """
    session = get_session(session_id)
    if not session:
        return JSONResponse({"error": "Session not found"}, status_code=404)

    selections = [
        StemSelection(
            stem_name=s["stem_name"],
            instrument_label=s["instrument_label"],
            output_choice=OutputChoice(s["output_choice"]),
        )
        for s in payload.get("selections", [])
    ]

    package = run_output_layer(
        selections,
        session["stem_collection"],
        session_id,
        audio_format=payload.get("audio_format", "wav"),
    )

    return {
        "status":     "complete",
        "session_id": session_id,
        "files": [
            {
                "stem_name":        f.stem_name,
                "instrument_label": f.instrument_label,
                "file_type":        f.file_type,
                "size_bytes":       f.size_bytes,
                "download_url":     f"/api/download/{session_id}/{os.path.basename(f.file_path)}",
            }
            for f in package.files
        ],
        "errors": package.errors,
    }


@router.get("/download/{session_id}/{filename}")
async def download(session_id: str, filename: str):
    """Serve a generated output file for download."""
    file_path = os.path.join("./outputs", session_id, filename)
    if not os.path.exists(file_path):
        return JSONResponse({"error": "File not found"}, status_code=404)
    return FileResponse(
        file_path,
        filename=filename,
        media_type="application/octet-stream",
    )