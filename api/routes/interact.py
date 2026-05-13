# -*- coding: utf-8 -*-
"""
Created on Mon May 11 10:48:41 2026

@author: Olive
"""

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from interaction.agent import build_selection_request, process_user_response
from interaction.models import UserSelectionResponse, StemSelection, OutputChoice
from orchestrator.session_store import get_session

router = APIRouter()


@router.get("/results/{session_id}")
async def get_results(session_id: str):
    """
    Return the instrument detection results for a completed analysis session.
    The frontend calls this to render the instrument selection UI.
    """
    session = get_session(session_id)
    if not session:
        return JSONResponse({"error": "Session not found"}, status_code=404)

    request = build_selection_request(
        session["classifications"],
        session["stem_collection"],
    )
    return {
        "status":                 "awaiting_selection",
        "confirmed_instruments":  request.confirmed_instruments,
        "unclear_stems":          request.unclear_stems,
        "track_metadata":         request.track_metadata,
    }


class SelectionPayload(BaseModel):
    selections: list[dict]


@router.post("/select/{session_id}")
async def submit_selection(session_id: str, payload: SelectionPayload):
    """
    Receive the user's instrument selections and output preferences.
    Triggers the output layer.
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
        for s in payload.selections
    ]

    response = UserSelectionResponse(selections=selections)
    validated = process_user_response(
        response, session["classifications"]
    )

    from output.router import run_output_layer
    package = run_output_layer(
        validated,
        session["stem_collection"],
        session_id,
    )

    return {
        "status":  "complete",
        "outputs": {
            "files": [
                {
                    "stem_name":        f.stem_name,
                    "instrument_label": f.instrument_label,
                    "file_type":        f.file_type,
                    "size_bytes":       f.size_bytes,
                    "download_url":     f"/api/download/{session_id}/{__import__('os').path.basename(f.file_path)}",
                }
                for f in package.files
            ],
            "errors": package.errors,
        }
    }