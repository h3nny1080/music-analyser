# -*- coding: utf-8 -*-
"""
Created on Sun May 10 12:56:11 2026

@author: Olive
"""

import os
import tempfile
import requests
from .youtube_match_agent import search_youtube_for_track, YouTubeCandidate
from .quality_gate import IngestionError
from .models import AudioObject

# Platforms we can get metadata from (to power the YouTube search)
METADATA_CAPABLE = {"spotify", "apple_music", "tidal", "soundcloud"}

def fetch_track_metadata(url: str, platform: str, token: str = None) -> dict:
    """
    Fetch title, artist, and duration from a streaming platform.
    Returns a dict with keys: title, artist, duration_seconds, album.
    """
    if platform == "spotify":
        return _spotify_metadata(url, token)
    if platform == "soundcloud":
        return _soundcloud_metadata(url)
    if platform in ("apple_music", "tidal"):
        return _parse_metadata_from_url(url, platform)
    raise IngestionError(f"Cannot fetch metadata for platform: {platform}")


def find_youtube_candidates(
    url: str,
    platform: str,
    token: str = None,
) -> tuple[dict, list[YouTubeCandidate]]:
    """
    Main entry point for streaming links.
    1. Fetches track metadata from the streaming platform.
    2. Searches YouTube for the best matches.
    Returns (metadata_dict, list_of_candidates) for the UI to present.
    The caller must then ask the user to confirm a candidate,
    and pass the confirmed URL to ingest_youtube().
    """
    metadata = fetch_track_metadata(url, platform, token)

    candidates = search_youtube_for_track(
        title=metadata["title"],
        artist=metadata["artist"],
        expected_duration_s=metadata.get("duration_seconds"),
    )

    if not candidates:
        raise IngestionError(
            f"Could not find '{metadata['artist']} - {metadata['title']}' "
            "on YouTube. Please upload the audio file directly."
        )

    return metadata, candidates


# ── Platform metadata fetchers ───────────────────────────────────────────────

def _spotify_metadata(url: str, token: str) -> dict:
    if not token:
        raise IngestionError(
            "A Spotify access token is required. "
            "Please connect your Spotify account in settings."
        )
    try:
        track_id = url.split("/track/")[1].split("?")[0]
    except IndexError:
        raise IngestionError(f"Could not parse Spotify track ID from: {url}")

    headers = {"Authorization": f"Bearer {token}"}
    r = requests.get(
        f"https://api.spotify.com/v1/tracks/{track_id}",
        headers=headers,
        timeout=10,
    )
    if r.status_code == 401:
        raise IngestionError("Spotify token expired. Please reconnect your account.")
    if r.status_code == 404:
        raise IngestionError("Spotify track not found.")
    r.raise_for_status()

    track = r.json()
    return {
        "title":            track.get("name", "Unknown"),
        "artist":           track["artists"][0]["name"] if track.get("artists") else "Unknown",
        "album":            track.get("album", {}).get("name", ""),
        "duration_seconds": track.get("duration_ms", 0) // 1000,
        "source_url":       url,
        "platform":         "spotify",
    }


def _soundcloud_metadata(url: str) -> dict:
    """
    SoundCloud doesn't require auth for public tracks.
    yt-dlp can extract metadata without downloading.
    """
    import yt_dlp
    ydl_opts = {"quiet": True, "no_warnings": True, "extract_flat": False}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
    return {
        "title":            info.get("title", "Unknown"),
        "artist":           info.get("uploader", "Unknown"),
        "duration_seconds": info.get("duration", 0),
        "source_url":       url,
        "platform":         "soundcloud",
    }


def _parse_metadata_from_url(url: str, platform: str) -> dict:
    """
    Fallback for Apple Music / Tidal where we don't have API access.
    Best-effort: parse the song name and artist from the URL path.
    The user will see the preview and can correct any mismatch.
    """
    # e.g. music.apple.com/gb/album/song-name/123456 → "song name"
    parts = [p for p in url.split("/") if p and not p.startswith("http")]
    guessed_title = parts[-2].replace("-", " ").title() if len(parts) >= 2 else "Unknown"
    return {
        "title":            guessed_title,
        "artist":           "Unknown",
        "duration_seconds": None,
        "source_url":       url,
        "platform":         platform,
        "note":             "Metadata estimated from URL — please confirm the preview",
    }