# -*- coding: utf-8 -*-
"""
Created on Mon May 11 10:31:38 2026

@author: Olive
"""

import yt_dlp
import re
from dataclasses import dataclass
from typing import Optional

@dataclass
class YouTubeCandidate:
    url: str
    title: str
    channel: str
    duration_seconds: int
    thumbnail_url: str
    score: float            # higher = better match

def search_youtube_for_track(
    title: str,
    artist: str,
    expected_duration_s: Optional[int] = None,
    max_results: int = 3,
) -> list[YouTubeCandidate]:
    """
    Search YouTube for a track by title + artist.
    Returns up to max_results candidates, ranked by match score.
    """
    query = f"{artist} - {title} official audio"

    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": True,       # don't download, just get metadata
        "default_search": f"ytsearch{max_results}",
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        results = ydl.extract_info(query, download=False)

    candidates = []
    for entry in results.get("entries", []):
        if not entry:
            continue
        candidate = YouTubeCandidate(
            url=f"https://www.youtube.com/watch?v={entry.get('id', '')}",
            title=entry.get("title", ""),
            channel=entry.get("uploader") or entry.get("channel", ""),
            duration_seconds=entry.get("duration", 0) or 0,
            thumbnail_url=entry.get("thumbnail", ""),
            score=_score_candidate(
                entry, title, artist, expected_duration_s
            ),
        )
        candidates.append(candidate)

    # Return best match first
    candidates.sort(key=lambda c: c.score, reverse=True)
    return candidates


def _score_candidate(
    entry: dict,
    expected_title: str,
    expected_artist: str,
    expected_duration_s: Optional[int],
) -> float:
    """
    Score a YouTube result against expected track metadata.
    Returns a float — higher is a better match.
    """
    score = 0.0
    result_title   = (entry.get("title") or "").lower()
    result_channel = (entry.get("uploader") or entry.get("channel") or "").lower()
    title_lower    = expected_title.lower()
    artist_lower   = expected_artist.lower()

    # Title match — exact substring scores highest
    if title_lower in result_title:
        score += 40
    else:
        # Partial word-level match
        title_words = set(re.findall(r'\w+', title_lower))
        result_words = set(re.findall(r'\w+', result_title))
        overlap = len(title_words & result_words)
        score += overlap * 8

    # Artist match in title or channel
    if artist_lower in result_title:
        score += 30
    if artist_lower in result_channel:
        score += 20

    # Penalise likely covers, karaoke, remixes, live versions
    penalty_terms = ["cover", "karaoke", "tribute", "remix", "live", "lyrics video"]
    for term in penalty_terms:
        if term in result_title:
            score -= 15

    # Prefer official uploads
    official_terms = ["official", "vevo", "records", "music"]
    for term in official_terms:
        if term in result_title or term in result_channel:
            score += 10
            break

    # Duration proximity — within 10 seconds of expected = good match
    if expected_duration_s and entry.get("duration"):
        diff = abs(entry["duration"] - expected_duration_s)
        if diff <= 10:
            score += 20
        elif diff <= 30:
            score += 10
        elif diff > 120:
            score -= 20   # likely wrong version

    return score