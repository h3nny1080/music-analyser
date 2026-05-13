# -*- coding: utf-8 -*-
"""
Created on Mon May 11 10:37:23 2026

@author: Olive
"""

# Instrument labels grouped by stem — CLAP scores each stem
# against the labels in its group rather than all 40 at once.
# This improves accuracy and cuts inference time.

LABELS_BY_STEM = {
    "vocals": [
        "lead vocals",
        "backing vocals",
        "choir",
        "vocal harmony",
        "spoken word",
    ],
    "drums": [
        "drum kit",
        "electronic drum machine",
        "kick drum",
        "snare drum",
        "cymbal",
        "congas",
        "bongos",
        "tabla",
    ],
    "bass": [
        "electric bass guitar",
        "upright double bass",
        "synthesizer bass",
        "bass clarinet",
    ],
    "guitar": [
        "acoustic guitar",
        "electric guitar",
        "classical guitar",
        "steel guitar",
        "banjo",
        "ukulele",
        "mandolin",
    ],
    "piano": [
        "piano",
        "electric piano",
        "organ",
        "synthesizer",
        "harpsichord",
        "accordion",
    ],
    "other": [
        "violin",
        "viola",
        "cello",
        "double bass",
        "trumpet",
        "trombone",
        "french horn",
        "tuba",
        "flute",
        "clarinet",
        "oboe",
        "saxophone",
        "harp",
        "xylophone",
        "marimba",
        "steel pan",
    ],
}

# Flat list for cases where you want to score against everything
ALL_LABELS = [label for labels in LABELS_BY_STEM.values() for label in labels]