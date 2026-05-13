# -*- coding: utf-8 -*-
"""
Created on Mon May 11 10:27:22 2026

@author: Olive
"""

from .detector import detect_input_type
from .youtube import ingest_youtube
from .streaming import fetch_track_metadata, find_youtube_candidates, _spotify_metadata, _soundcloud_metadata, _parse_metadata_from_url
from .file_upload import ingest_file
from .models import AudioObject
from .quality_gate import IngestionError
from .youtube_match_agent import search_youtube_for_track, YouTubeCandidate
from .streaming import find_youtube_candidates, fetch_track_metadata

__all__ = [
    "detect_input_type",
    "ingest_youtube",
    "fetch_track_metadata",
    "find_youtube_candidates",
    "_spotify_metadata",
    "_soundcloud_metadata",
    "_parse_metadata_from_url",
    
    "ingest_file",
    "AudioObject",
    "IngestionError",
    "search_youtube_for_track",
    "YouTubeCandidate",
    "find_youtube_candidates",
    "fetch_track_metadata",
]