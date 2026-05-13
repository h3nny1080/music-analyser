# -*- coding: utf-8 -*-
"""
Created on Sat May  9 15:56:23 2026

@author: Olive
"""

import os
import tempfile
import yt_dlp
from .normaliser import normalise_file
from .models import AudioObject

def ingest_youtube(url: str) -> AudioObject:
    """
    Download audio from a YouTube URL using yt-dlp,
    convert to WAV, then normalise.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        wav_path = os.path.join(tmpdir, "audio.wav")

        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": os.path.join(tmpdir, "audio.%(ext)s"),
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "wav",
                    "preferredquality": "0",   # lossless
                }
            ],
            "quiet": True,
            "no_warnings": True,
            # Retry on transient errors
            "retries": 3,
            "fragment_retries": 3,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)

        metadata = {
            "title":      info.get("title", "Unknown"),
            "artist":     info.get("uploader", "Unknown"),
            "duration":   info.get("duration", 0),
            "source_url": url,
            "platform":   "youtube",
        }

        return normalise_file(wav_path, source_type="youtube", metadata=metadata)