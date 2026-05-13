# -*- coding: utf-8 -*-
"""
Created on Mon May 11 10:49:18 2026

@author: Olive
"""

import uuid
from typing import Optional

_sessions: dict[str, dict] = {}

def create_session(classifications: dict, stem_collection) -> str:
    """Store pipeline state, return a session ID."""
    session_id = str(uuid.uuid4())
    _sessions[session_id] = {
        "classifications":  classifications,
        "stem_collection":  stem_collection,
    }
    return session_id

def get_session(session_id: str) -> Optional[dict]:
    return _sessions.get(session_id)

def delete_session(session_id: str):
    _sessions.pop(session_id, None)