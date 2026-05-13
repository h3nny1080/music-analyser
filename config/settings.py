# -*- coding: utf-8 -*-
"""
Created on Mon May 11 10:03:46 2026

@author: Olive
"""

from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    spotify_client_id: str = ""
    spotify_client_secret: str = ""
    max_upload_mb: int = 100
    temp_dir: str = "/tmp/music-analyser"
    output_dir: str = "./outputs"
    lilypond_path: str = r"C:\Program Files (x86)\lilypond-2.26.0-mingw-x86_64\lilypond-2.26.0\bin\lilypond.EXE"

    class Config:
        env_file = ".env"

settings = Settings()