# -*- coding: utf-8 -*-
"""
Created on Mon May 11 12:50:04 2026

@author: Olive
"""

from typing import Optional

_progress: dict[str, dict] = {}

def set_progress(session_id: str, stage: str, percent: int, message: str = ""):
    _progress[session_id] = {
        "stage":   stage,
        "percent": percent,
        "message": message,
    }

def get_progress(session_id: str) -> Optional[dict]:
    return _progress.get(session_id, {
        "stage":   "queued",
        "percent": 0,
        "message": "Waiting to start…",
    })

def clear_progress(session_id: str):
    _progress.pop(session_id, None)