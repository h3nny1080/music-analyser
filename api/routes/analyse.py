# -*- coding: utf-8 -*-
"""
Created on Sun May 10 13:03:17 2026

@author: Olive
"""

from fastapi import APIRouter, UploadFile, File, Form
from fastapi.responses import JSONResponse
from orchestrator.pipeline import start_ingestion, confirm_youtube_match

router = APIRouter()

@router.post("/analyse")
async def analyse(
    url: str = Form(default=None),
    file: UploadFile = File(default=None),
    spotify_token: str = Form(default=None),
):
    """
    Submit a URL or file. If a streaming link is provided, returns
    YouTube candidates for the frontend to display for confirmation.
    """
    if url:
        result = await start_ingestion(url, spotify_token=spotify_token)
    elif file:
        file_bytes = await file.read()
        result = await start_ingestion(file_bytes, filename=file.filename)
    else:
        return JSONResponse({"error": "Provide a URL or upload a file"}, status_code=400)

    if result["status"] == "confirm":
        # Return candidates to the frontend — don't serialise the AudioObject
        return {
            "status":     "confirm",
            "metadata":   result["metadata"],
            "candidates": [
                {
                    "url":              c.url,
                    "title":            c.title,
                    "channel":          c.channel,
                    "duration_seconds": c.duration_seconds,
                    "thumbnail_url":    c.thumbnail_url,
                }
                for c in result["candidates"]
            ],
        }

    return result


@router.post("/analyse/confirm")
async def confirm(youtube_url: str = Form(...)):
    """
    Called when the user confirms a YouTube candidate.
    Proceeds with ingestion and the full analysis pipeline.
    """
    result = await confirm_youtube_match(youtube_url)
    return result