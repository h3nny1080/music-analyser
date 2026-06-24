# -*- coding: utf-8 -*-
"""
Spotify match agent.
Fetches track metadata from the Spotify Web API, then searches YouTube
for the best-matching audio candidates to present to the user for confirmation.
"""

import re
import os
import requests
from dataclasses import dataclass
from typing import Optional

from .quality_gate import IngestionError
from .youtube_match_agent import search_youtube_for_track, YouTubeCandidate


@dataclass
class SpotifyMetadata:
    title: str
    artist: str
    album: str
    duration_seconds: int
    source_url: str


def fetch_spotify_metadata(url: str, token: str) -> SpotifyMetadata:
    """
    Fetch track metadata from the Spotify Web API.
    Requires a valid OAuth access token.
    """
    token = os.environ.get("SPOTIFY_CLIENT_ID")
    if not token:
        raise IngestionError(
            "A Spotify access token is required. "
            "Please connect your Spotify account in settings."
        )

    match = re.search(r"/track/([A-Za-z0-9]+)", url)
    if not match:
        raise IngestionError(f"Could not parse a Spotify track ID from: {url!r}")
    track_id = match.group(1)

    r = requests.get(
        f"https://api.spotify.com/v1/tracks/{track_id}",
        headers={"Authorization": f"Bearer {token}"},
        timeout=10,
    )
    if r.status_code == 401:
        raise IngestionError("Spotify token expired. Please reconnect your account.")
    if r.status_code == 404:
        raise IngestionError("Spotify track not found.")
    r.raise_for_status()

    track = r.json()
    return SpotifyMetadata(
        title=track.get("name", "Unknown"),
        artist=track["artists"][0]["name"] if track.get("artists") else "Unknown",
        album=track.get("album", {}).get("name", ""),
        duration_seconds=track.get("duration_ms", 0) // 1000,
        source_url=url,
    )


def search_spotify_track_on_youtube(
    url: str,
    token: str,
) -> tuple[SpotifyMetadata, list[YouTubeCandidate]]:
    """
    Main entry point.
    1. Fetches track metadata from Spotify.
    2. Searches YouTube for the best-matching candidates.
    Returns (metadata, candidates) — the caller presents candidates to the user
    and passes the confirmed YouTube URL to ingest_youtube().
    """
    metadata = fetch_spotify_metadata(url, token)

    candidates = search_youtube_for_track(
        title=metadata.title,
        artist=metadata.artist,
        expected_duration_s=metadata.duration_seconds,
    )

    if not candidates:
        raise IngestionError(
            f"Could not find \"{metadata.artist} – {metadata.title}\" on YouTube. "
            "Try uploading an audio file directly."
        )

    return metadata, candidates
