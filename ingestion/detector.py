# -*- coding: utf-8 -*-
"""
Created on Sat May  9 15:55:59 2026

@author: Olive
"""

import re

YOUTUBE_PATTERN    = re.compile(r"(https?://)?(www\.)?(youtube\.com/watch\?v=|youtu\.be/)[\w\-]+")
SPOTIFY_PATTERN    = re.compile(r"https?://open\.spotify\.com/track/[\w]+")
APPLE_PATTERN      = re.compile(r"https?://music\.apple\.com/.+/album/.+")
SOUNDCLOUD_PATTERN = re.compile(r"https?://(www\.)?soundcloud\.com/[\w\-]+/[\w\-]+")
TIDAL_PATTERN      = re.compile(r"https?://(www\.)?tidal\.com/browse/track/\d+")

def detect_input_type(input_str: str) -> str:
    """
    Returns one of: "youtube", "spotify", "apple_music",
                    "soundcloud", "tidal", "file"
    """
    s = input_str.strip()
    if YOUTUBE_PATTERN.search(s):    return "youtube"
    if SPOTIFY_PATTERN.search(s):    return "spotify"
    if APPLE_PATTERN.search(s):      return "apple_music"
    if SOUNDCLOUD_PATTERN.search(s): return "soundcloud"
    if TIDAL_PATTERN.search(s):      return "tidal"
    return "file"