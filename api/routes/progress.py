# -*- coding: utf-8 -*-
"""
Created on Mon May 11 12:50:45 2026

@author: Olive
"""

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from orchestrator.progress_store import get_progress

router = APIRouter()

@router.get("/progress/{session_id}")
async def progress(session_id: str):
    data = get_progress(session_id)
    if not data:
        return JSONResponse({"error": "Session not found"}, status_code=404)
    return data