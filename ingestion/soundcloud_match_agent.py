# -*- coding: utf-8 -*-
"""
SoundCloud ingestion using scdl.
Downloads the track at the given URL directly as an MP3, then normalises
it into an AudioObject ready for the pipeline.
"""

import os
import subprocess
import sys
import tempfile
import glob

from .normaliser import normalise_file
from .models import AudioObject
from .quality_gate import IngestionError


def ingest_soundcloud(url: str) -> AudioObject:
    """
    Download audio from a SoundCloud URL using scdl,
    then normalise into an AudioObject.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        scdl_exe = os.path.join(os.path.dirname(sys.executable), "scdl.exe")
        try:
            subprocess.run(
                [
                    scdl_exe,
                    "-l", url,
                    "--path", tmpdir,
                    "--onlymp3",
                    "--no-playlist",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
        except subprocess.CalledProcessError as e:
            raise IngestionError(
                f"scdl failed to download {url!r}.\n{e.stderr.strip()}"
            ) from e

        mp3_files = glob.glob(os.path.join(tmpdir, "*.mp3"))
        if not mp3_files:
            raise IngestionError(
                f"scdl ran successfully but no MP3 was found for {url!r}. "
                "The track may be private or region-locked."
            )

        mp3_path = mp3_files[0]
        track_name = os.path.splitext(os.path.basename(mp3_path))[0]

        # scdl names files as "Artist - Title" where possible
        parts = track_name.split(" - ", 1)
        artist = parts[0].strip() if len(parts) == 2 else "Unknown"
        title  = parts[1].strip() if len(parts) == 2 else track_name

        metadata = {
            "title":      title,
            "artist":     artist,
            "source_url": url,
            "platform":   "soundcloud",
        }

        return normalise_file(mp3_path, source_type="soundcloud", metadata=metadata)
